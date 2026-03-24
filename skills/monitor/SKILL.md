# Monitor Agent Skill — Mission Control Sweeps

Use this skill whenever Jarvis (or a sub-agent) needs to perform the Mission Control monitoring sweep.

## Triggers
- "check stocks", "MicroCenter prices", "system health", "cron drift"
- Any task with >15 minutes remaining (PowerSpec must be online)
- Standing sweep every 5 minutes (set cron/heartbeat accordingly)

## Prereqs
- Access to localhost Mission Control backend (`http://localhost:3001`)
- Tailscale logged in on Mac + PowerSpec (`tailscale status`)
- SSH key trusted by `ericf@100.67.128.123`

## Sweep Checklist (every 5 minutes)

### 0. Auth Pre-Flight (MANDATORY — runs first)
```bash
gog gmail search "newer_than:1h" --max 1 --account ericfbrown1@gmail.com
gh auth status
```
- If `gog` returns `invalid_grant` or timeout → immediately run:
  `gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent`
- If `gh` fails → alert Eric via Telegram
- Log any auth failure to `memory/incidents.jsonl`
- If auth is broken, pause all credential-dependent work until restored
- **This prevents cascading cron failures from dead tokens**

### 1. App Health
```bash
curl -fsS http://localhost:3000/health   # Frontend
curl -fsS http://localhost:3001/health   # Backend
pm2 status                                # Process manager
```
Restart + alert if anything fails.

### 2. Dashboard Parity
- Fetch `curl -fsS http://localhost:3001/tasks | jq '.tasks[] | {id, status, progress}'`
- Compare against Mission Control home, Agents conveyor, and Task Board UI
- Any mismatch = critical incident → log to `memory/incidents.jsonl` and alert Eric
- Schema: `{"timestamp":"<ISO>","agent":"monitor","project":"mission-control","error_category":"dashboard","error_summary":"<desc>","resolution":"unresolved","known_failure":null}`

### 3. Git Hygiene
```bash
for repo in $(find /Users/ericbrown -maxdepth 3 -name '.git' -type d 2>/dev/null | sed 's/\.git$//'); do
  echo "=== $repo ===" && cd "$repo" && git status -sb && cd -
done
```
- If dirty >2h or no remote configured → open Task Board ticket
- **Auto-fix:** If project directory has no `.git`, log it and create a task to initialize the repo
- Reference: IBM (Mar 2026) — observable pipelines with logging

### 4. PowerSpec Readiness
```bash
tailscale ping remote-coder-main          # Reachability
ssh ericf@100.67.128.123 nvidia-smi       # GPU status
```
- If unreachable: attempt 3 wake retries (30s apart), log to `memory/incidents.jsonl`
- If still unreachable after 3 attempts: alert Eric via Telegram
- **Idle Alert:** If PowerSpec GPU util <5% while tasks remain queued, alert Conductor to offload work immediately
- When any running task has `remainingMinutes > 15`, keep PowerSpec online
- Reference: Mirantis (Feb 2026) — hybrid AI workload balancing; GoWorkWize (Mar 2026) — explicit Mac/PC allocation

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

### 7. Observability Pipeline
- Verify OpenTelemetry collector, Prometheus, and Grafana are ingesting data
- Restart collectors if ingestion stalled
- Reference: IBM (Mar 2026) — AI-assisted observability; Spacelift (Jan 2026) — proactive alerts

### 8. Deliverable Sweep (Grok Audit)
- For any task marked `running` with a deliverable target (email/doc):
  - Check if deliverable was already sent but status not updated → fix status
  - Flag stale running tasks (>24h without progress updates) as incidents

### 9. Dead Link Scan (Grok Audit — weekly)
- Crawl all Mission Control nav items (`/`, `/agents`, `/tasks`, `/cron`, `/health`, `/comms`, `/memory`, `/alerts`, `/settings`)
- Flag pages returning errors, placeholder content, or non-functional links
- Log broken elements in `memory/incidents.jsonl`
- Reference: Testomat.io (Feb 2026) — accessibility testing as essential requirement

### 10. Status Report
- Send summary to Telegram or Task Board when all checks pass
- Send immediately when any check fails
- Include: timestamp, pass/fail per check, incident count, PowerSpec utilization %
- Format:
```
🔍 Monitor Sweep [<timestamp>]
✅/❌ App Health: <status>
✅/❌ Dashboard Parity: <status>
✅/❌ Git Hygiene: <n> repos clean, <n> dirty
✅/❌ PowerSpec: <online/offline> GPU <util>%
✅/❌ Cron Drift: <status>
✅/❌ Deliverables: <n> stale tasks
📊 Incidents logged: <n>
```

## Escalation Rules
- PowerSpec offline >5 min with queued tasks → CRITICAL incident, alert Eric
- Dashboard parity mismatch → freeze deployments, notify Quality + Coder
- Auth failures (gog/gh) → switch to fallback channels before continuing
- Stale running task >24h → alert Eric + open incident

## Root Cause Analysis (on every failure)
When ANY sweep step fails:
1. Log the failure to `memory/incidents.jsonl` with full schema (including root_cause and prevention fields)
2. Run 5-Whys analysis: ask "Why?" at least 3 times to get past symptoms
3. Implement the fix immediately (don't just document it)
4. Update the relevant SKILL.md or AGENTS.md section so the failure class is prevented
5. Add a monitoring check that would catch recurrence
6. If the same error category appears >2 times, escalate to Eric with a structural fix proposal

## References
- IBM "Observability Trends 2026" — AI-assisted, open-standard telemetry
- Spacelift "11 Observability Best Practices (Jan 2026)" — metrics/logs/traces tied to KPIs
- Mirantis "AI Workloads: Management and Best Practices (Feb 2026)" — hybrid workload scheduling
- GoWorkWize "Mac vs PC in a Hybrid Workplace (Mar 2026)" — explicit device allocation
- Testomat.io "Software Testing Trends (Feb 2026)" — continuous testing, accessibility, deliverable validation
