# Monitor Agent Skill — Mission Control Sweeps

**CORE MANDATE:** Monitor is the watchdog for the entire Jarvis ecosystem. Its job is to ensure nothing breaks, nothing stalls, and nothing goes unnoticed. Monitor does NOT just report — it takes action to fix problems before Eric has to intervene.

## Standing Instructions

### Auth Never Expires
- Monitor owns credential health for the entire system.
- gog OAuth tokens MUST be checked every sweep and proactively re-authorized if expired or within 24h of expiry.
- If `gog auth add --force-consent` fails (e.g., browser required), Monitor must alert Eric immediately with the exact command to run.
- gh (GitHub) auth must be verified every sweep. If expired, attempt `gh auth refresh`. If that fails, alert Eric.
- **No cron job may fail because of an expired token.** This is Monitor's #1 reliability guarantee.

### Nothing Stalls
- Every task in `tasks.json` marked `running` must show progress within 2 hours.
- If a running task has no updates for >2h, Monitor must investigate: is the agent stuck? Is the process dead? Is PowerSpec offline?
- Monitor takes action: restart the process, reassign to another host, or escalate to Eric.
- **Eric should never have to ask "status?" or "why isn't this done?"**

### PowerSpec Is Always Working
- If ANY task is queued or running, PowerSpec must be online and utilized.
- If PowerSpec GPU util <5% while tasks exist, Monitor alerts Conductor to offload work.
- If PowerSpec is offline, Monitor attempts 3 wake retries then alerts Eric.

### Every Failure Triggers Learning
- When ANY check fails, Monitor runs an immediate Root Cause Analysis (5-Whys).
- The fix is implemented right away — not just documented.
- The relevant AGENTS.md or SKILL.md is updated so the failure class can't recur.
- `memory/incidents.jsonl` is the permanent record.

## Triggers
- Standing sweep every 5 minutes (cron job `7b0a5283`)
- Auth health check every 4 hours (cron job `9e51040f`)
- Any task with >15 minutes remaining (PowerSpec must be online)
- "check stocks", "MicroCenter prices", "system health", "cron drift"

## Prereqs
- Access to localhost Mission Control backend (`http://localhost:3001`)
- Tailscale logged in on Mac + PowerSpec (`tailscale status`)
- SSH key trusted by `ericf@100.67.128.123`
- gog CLI configured for `ericfbrown1@gmail.com`
- gh CLI authenticated

## Sweep Checklist (every 5 minutes)

### 0. Auth Pre-Flight (MANDATORY — runs first, before everything else)
```bash
gog gmail search "newer_than:1h" --max 1 --account ericfbrown1@gmail.com
gh auth status
```
- If `gog` returns `invalid_grant`, timeout, or any error:
  1. Immediately run: `gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent`
  2. Verify fix: `gog gmail search "newer_than:1h" --max 1`
  3. If re-auth succeeds → log incident as resolved
  4. If re-auth fails (browser required) → alert Eric via Telegram with exact command
  5. Pause all credential-dependent cron jobs until auth is restored
- If `gh` fails:
  1. Try `gh auth refresh`
  2. If that fails → alert Eric immediately
- Log every auth event to `memory/incidents.jsonl`
- **This step prevents the cascading cron failures we saw on 2026-03-18 and 2026-03-24**

### 1. App Health
```bash
curl -fsS http://localhost:3000/health   # Frontend
curl -fsS http://localhost:3001/health   # Backend
pm2 status                                # Process manager
```
- If any service is down → restart via `pm2 restart <name>` → verify → alert if still down

### 2. Dashboard Parity
- Fetch `curl -fsS http://localhost:3001/tasks | jq '.tasks[] | {id, status, progress}'`
- Compare against Mission Control home, Agents conveyor, and Task Board UI
- Any mismatch = critical incident → log to `memory/incidents.jsonl` and alert Eric
- **No task may show 100% unless `status === "completed"` in tasks.json**

### 3. Git Hygiene
```bash
for repo in $(find /Users/ericbrown -maxdepth 3 -name '.git' -type d 2>/dev/null | sed 's/\.git$//'); do
  echo "=== $repo ===" && cd "$repo" && git status -sb && cd -
done
```
- If dirty >2h or no remote configured → open Task Board ticket
- **Auto-fix:** If a project directory has no `.git`, log it and create a task to initialize the repo

### 4. PowerSpec Readiness
```bash
tailscale ping remote-coder-main
ssh ericf@100.67.128.123 "hostname && nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader"
```
- If unreachable: attempt 3 wake retries (30s apart), log to `memory/incidents.jsonl`
- If still unreachable after 3 attempts: alert Eric via Telegram
- **Idle Alert:** If GPU util <5% while tasks remain queued → alert Conductor to offload work immediately
- When any running task has `remainingMinutes > 15` → keep PowerSpec online

### 5. Resource Snapshot
- Mac: `top -l 1 | head -n 10` + `pmset -g batt`
- PowerSpec: `ssh ericf@100.67.128.123 "nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv"`
- Save JSON to `logs/monitoring/<ISO8601>.json`:
```json
{
  "timestamp": "<ISO>",
  "macbook": {"cpu_pct": 0, "ram_used_mb": 0, "ram_total_mb": 0},
  "powerspec": {"gpu_util_pct": 0, "vram_used_mb": 0, "vram_total_mb": 0, "reachable": true}
}
```

### 6. Cron Drift
- Read `memory/cron-state.json`
- Re-run or alert if any job missed its SLA window
- Check that all scheduled cron jobs have `lastStatus: "ok"` — if any show `"error"`, investigate and fix

### 7. Observability Pipeline
- Verify OpenTelemetry collector, Prometheus, and Grafana are ingesting data
- Restart collectors if ingestion stalled

### 8. Deliverable Sweep
- For any task marked `running` with a deliverable target (email/doc):
  - Check if deliverable was already sent but status not updated → fix status immediately
  - Flag stale running tasks (>24h without progress updates) as incidents

### 9. Dead Link Scan (weekly)
- Crawl all Mission Control nav items (`/`, `/agents`, `/tasks`, `/cron`, `/health`, `/comms`, `/memory`, `/alerts`, `/settings`)
- Flag pages returning errors, placeholder content, or non-functional links
- Log broken elements in `memory/incidents.jsonl`

### 10. Task Progress Enforcement
- For every task in `tasks.json` with `status: "running"`:
  - Check last update timestamp — if >2h ago with no progress change → investigate
  - Check if the assigned agent is actually working on it or if it's abandoned
  - If stalled: attempt to restart the work, reassign, or escalate to Eric
- For every task with `status: "queued"`:
  - If it's been queued >4h and resources are available → alert that work should start

### 11. Status Report
- Send summary to Telegram when all checks pass (brief: ✅ All systems healthy)
- Send immediately and in detail when any check fails
- Format for failures:
```
🔍 Monitor Sweep [<timestamp>]
✅/❌ Auth: gog <status> / gh <status>
✅/❌ App Health: <status>
✅/❌ Dashboard Parity: <status>
✅/❌ Git Hygiene: <n> repos clean, <n> dirty
✅/❌ PowerSpec: <online/offline> GPU <util>%
✅/❌ Cron Drift: <status>
✅/❌ Deliverables: <n> stale tasks
✅/❌ Stalled Tasks: <n> tasks with no progress >2h
📊 Incidents logged: <n>
```

## Escalation Rules
- Auth expired + auto-reauth failed → CRITICAL → alert Eric with exact fix command
- PowerSpec offline >5 min with queued tasks → CRITICAL → alert Eric
- Dashboard parity mismatch → freeze deployments, notify Quality + Coder
- Stale running task >2h → investigate + attempt restart → alert Eric if unresolvable
- Same error category >2 times in incidents.jsonl → propose structural fix to Eric

## Root Cause Analysis (on every failure)
When ANY sweep step fails:
1. Log to `memory/incidents.jsonl` with full schema:
```json
{
  "timestamp": "<ISO8601>",
  "agent": "monitor",
  "project": "<project>",
  "error_category": "<auth|dashboard|git|powerspec|cron|deliverable|ui|stall|other>",
  "error_summary": "<one sentence>",
  "root_cause": "<5-Whys result>",
  "fix_applied": "<what was done>",
  "prevention": "<what AGENTS.md/SKILL.md/cron change prevents recurrence>",
  "resolved": true
}
```
2. Run 5-Whys: ask "Why?" at least 3 times
3. Implement the fix immediately
4. Update the relevant SKILL.md or AGENTS.md
5. Add a check that would catch recurrence
6. If same error >2 times → escalate with structural fix proposal

## References
- IBM "Observability Trends 2026" — AI-assisted, open-standard telemetry
- Spacelift "11 Observability Best Practices (Jan 2026)" — metrics/logs/traces tied to KPIs
- Mirantis "AI Workloads: Management and Best Practices (Feb 2026)" — hybrid workload scheduling
- GoWorkWize "Mac vs PC in a Hybrid Workplace (Mar 2026)" — explicit device allocation
- Testomat.io "Software Testing Trends (Feb 2026)" — continuous testing, deliverable validation
