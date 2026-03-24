# Monitor Agent Skill — Mission Control Sweeps

**CORE MANDATE:** Monitor is the watchdog for the entire Jarvis ecosystem. Its job is to ensure nothing breaks, nothing stalls, and nothing goes unnoticed. Monitor does NOT just report — it takes action to fix problems before Eric has to intervene.

## Standing Instructions

### Auth Never Expires
- Monitor owns credential health for the entire system.
- gog OAuth tokens MUST be checked every sweep and proactively re-authorized if expired.
- If `gog auth add --force-consent` fails (e.g., browser required), alert Eric immediately with the exact command.
- gh (GitHub) auth must be verified every sweep. If expired, attempt `gh auth refresh`. If that fails, alert Eric.
- **No cron job may fail because of an expired token.** This is Monitor's #1 reliability guarantee.

### Nothing Stalls
- Every task in `tasks.json` marked `running` must show progress within 2 hours.
- If a running task has no updates for >2h, Monitor must investigate and take action: restart, reassign, or escalate.
- **Eric should never have to ask "status?" or "why isn't this done?"**

### PowerSpec Is Always Working
- If ANY task is queued or running, PowerSpec must be online and utilized.
- If PowerSpec GPU util <5% while tasks exist, Monitor alerts Conductor to offload work.
- If PowerSpec is offline, Monitor attempts 3 wake retries then alerts Eric.
- See `POWERSPEC.md` for full mandatory execution policy.

### Every Failure Triggers Learning
- When ANY check fails, Monitor runs an immediate Root Cause Analysis (5-Whys).
- The fix is implemented right away — not just documented.
- The relevant SKILL.md, DELEGATION.md, PIPELINE.md, or companion file is updated so the failure class can't recur.
- `memory/incidents.jsonl` is the permanent record. See `INCIDENTS.md` for full schema.

### Workspace File Size Hygiene
- During Git hygiene sweeps, check the byte size of all workspace .md files.
- If ANY file exceeds 10KB, flag it for splitting.
- AGENTS.md must stay under 5KB (it's the bootstrap file — truncation kills agent awareness).
- Heavy content belongs in companion files: DELEGATION.md, PIPELINE.md, POWERSPEC.md, INCIDENTS.md.
- **Root cause lesson:** On 2026-03-23, AGENTS.md grew to 37KB and 52% was truncated during bootstrap, meaning agents only read half the rules. This caused multiple failures because agents didn't see completion gates, PowerSpec policy, or deliverable verification rules.

### Dashboard Is Always Current
- `tasks.json` must reflect real-time state of ALL projects at ALL times.
- New tasks must appear on the Task Board the moment they're requested.
- Progress updates must happen at every milestone (25→50→75→100).
- No task hits 100% without proof (commit SHA for code, Gmail ID for reports).
- Monitor verifies every 5 minutes; stale entries (>2h no update while running) trigger investigation + action.

### Context-Switching Prevention
- Monitor tracks which tasks are actively being worked on vs. abandoned.
- If Jarvis or any agent starts a new task without completing the current one, Monitor flags it.
- **Root cause lesson:** On 2026-03-22/23, Steps 1-2 stalled for 12+ hours because Jarvis kept pivoting to new requests (UI polish, Grok audit, model routing) instead of finishing the pm2 cutover. Monitor's stale task alerting now catches this pattern.

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

### 0. Auth Pre-Flight (MANDATORY — runs first)
```bash
gog gmail search "newer_than:1h" --max 1 --account ericfbrown1@gmail.com
gh auth status
```
- If `gog` fails → immediately run: `gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent`
- If `gh` fails → try `gh auth refresh` → if still fails, alert Eric
- Log every auth event to `memory/incidents.jsonl`
- Pause all credential-dependent work until auth is restored

### 1. App Health
```bash
curl -fsS http://localhost:3000/health   # Frontend
curl -fsS http://localhost:3001/health   # Backend
pm2 status                                # Process manager
```
If down → `pm2 restart <name>` → verify → alert if still down.

### 2. Dashboard Parity
- Fetch `curl -fsS http://localhost:3001/tasks | jq '.tasks[] | {id, status, progress}'`
- Verify all UI views match backend data
- **No task may show 100% unless `status === "completed"` in tasks.json**
- Mismatches = critical incident → log + alert Eric

### 3. Git Hygiene
```bash
for repo in $(find /Users/ericbrown -maxdepth 3 -name '.git' -type d 2>/dev/null | sed 's/\.git$//'); do
  echo "=== $repo ===" && cd "$repo" && git status -sb && cd -
done
```
- Dirty >2h or no remote → Task Board ticket
- No `.git` in project dir → log + create initialization task
- **File size check:** Flag any workspace .md file >10KB for splitting

### 4. PowerSpec Readiness
```bash
tailscale ping remote-coder-main
ssh ericf@100.67.128.123 "hostname && nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader"
```
- Unreachable → 3 retries (30s) → alert Eric
- GPU util <5% + queued tasks → alert Conductor to offload
- Running task with >15min remaining → keep PowerSpec online

### 5. Resource Snapshot
Save to `logs/monitoring/<ISO8601>.json`:
```json
{"timestamp":"<ISO>","macbook":{"cpu_pct":0,"ram_used_mb":0},"powerspec":{"gpu_util_pct":0,"vram_used_mb":0,"vram_total_mb":16303,"reachable":true}}
```

### 6. Cron Drift
- Read `memory/cron-state.json` — re-run or alert if any job missed SLA
- Check all cron jobs have `lastStatus: "ok"` — investigate errors

### 7. Observability Pipeline
- Verify telemetry collectors are ingesting data; restart if stalled

### 8. Deliverable Sweep
- Running tasks with deliverable targets: check if already sent but status not updated → fix immediately
- Stale running tasks (>24h no progress) → flag as incident

### 9. Dead Link Scan (weekly)
- Crawl all Mission Control nav items
- Flag errors, placeholders, non-functional links → log in `memory/incidents.jsonl`

### 10. Task Progress Enforcement
- Running tasks with no update >2h → investigate: agent stuck? process dead? PowerSpec offline?
- Queued tasks >4h with available resources → alert that work should start
- **Context-switch detection:** If an agent started a new task without completing the current one → flag it

### 11. Status Report
Brief when healthy: `✅ All systems healthy`
Detailed on failure:
```
🔍 Monitor Sweep [<timestamp>]
✅/❌ Auth: gog <status> / gh <status>
✅/❌ App Health: <status>
✅/❌ Dashboard Parity: <status>
✅/❌ Git Hygiene: <n> repos clean, <n> dirty, <n> files >10KB
✅/❌ PowerSpec: <online/offline> GPU <util>%
✅/❌ Cron Drift: <status>
✅/❌ Deliverables: <n> stale tasks
✅/❌ Stalled Tasks: <n> with no progress >2h
📊 Incidents logged: <n>
```

## Escalation Rules
- Auth expired + auto-reauth failed → CRITICAL → alert Eric with exact command
- PowerSpec offline >5 min with queued tasks → CRITICAL → alert Eric
- Dashboard parity mismatch → freeze deployments, notify Quality + Coder
- Stale running task >2h → investigate + attempt restart → alert Eric if unresolvable
- Same error category >2 times → propose structural fix to Eric
- Workspace file >10KB → flag for splitting before next commit

## Root Cause Analysis (on every failure)
1. Log to `memory/incidents.jsonl` with full schema (see `INCIDENTS.md`)
2. Run 5-Whys (3 times minimum)
3. Implement fix immediately
4. Update relevant SKILL.md or companion file
5. Add monitoring check for recurrence
6. Same error >2 times → escalate with structural fix

## Key Lessons Learned (embedded in standing instructions)
| Incident | Root Cause | Prevention in This Skill |
|----------|-----------|--------------------------|
| gog token expired → 7 failed cron jobs | No automated auth check | Auth Pre-Flight (Step 0) runs every sweep |
| Dashboard showed false 100% | Time-based progress | Dashboard Parity (Step 2) enforces status === completed |
| PowerSpec idle while tasks queued | Usage was optional | PowerSpec Readiness (Step 4) alerts on idle GPU |
| AGENTS.md grew to 37KB, 52% truncated | Rules appended without size check | Git Hygiene (Step 3) flags files >10KB |
| Steps stalled 12+ hours | Context-switching, no enforcement | Task Progress Enforcement (Step 10) catches >2h stalls |
| Placeholder Terminal link shipped | No UI verification | Dead Link Scan (Step 9) crawls all nav items |
| Report marked complete without email | No deliverable gate | Deliverable Sweep (Step 8) verifies proof |

## References
- IBM "Observability Trends 2026" — AI-assisted, open-standard telemetry
- Spacelift "11 Observability Best Practices (Jan 2026)" — metrics/logs/traces tied to KPIs
- Mirantis "AI Workloads (Feb 2026)" — hybrid workload scheduling
- GoWorkWize "Mac vs PC (Mar 2026)" — explicit device allocation
- Testomat.io "Testing Trends (Feb 2026)" — continuous testing, deliverable validation
