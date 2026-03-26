# Monitor Agent Skill — Mission Control Sweeps

**CORE MANDATE:** Monitor is the watchdog for the entire Jarvis ecosystem. Its job is to ensure nothing breaks, nothing stalls, and nothing goes unnoticed. Monitor does NOT just report — it takes action to fix problems before Eric has to intervene.

## Standing Instructions

### Auth Never Expires (with Auto-Fallback)
- Monitor owns credential health for the entire system.
- gog OAuth tokens MUST be checked every sweep.
- **If gog fails:** Do NOT attempt `gog auth add --force-consent` (requires browser, always fails in cron/agent context). Instead:
  1. Set `auth_healthy: false` in `memory/cron-state.json` (circuit breaker — stops cron storms)
  2. Set `memory/auth-fallback-state.json` to route Gmail/Calendar/Sheets/Drive through Zapier MCP
  3. Log incident to `memory/incidents.jsonl`
  4. Send Telegram alert to Eric with the exact manual fix command
  5. All agents route Google operations through Zapier MCP until auth is restored
- **selfheal.sh** handles steps 1-4 automatically every 10 minutes. Monitor verifies the state is consistent.
- gh (GitHub) auth must be verified every sweep. If expired, attempt `gh auth refresh`. If that fails, alert Eric.
- **No cron job may fail because of an expired token.** Circuit breaker + Zapier fallback guarantee this.

### Nothing Stalls
- Every task in `tasks.json` marked `running` must show progress within 2 hours.
- If a running task has no updates for >2h, Monitor must investigate and take action: restart, reassign, or escalate.
- **Subagent watchdog:** When a subagent (Coder, Researcher, etc.) is spawned for a task, Monitor tracks its session. If the subagent hasn't reported back within 10 minutes, Monitor must:
  1. Check if the subagent session is still alive
  2. If dead/timed out → immediately re-spawn with the same task
  3. Alert Eric that a restart occurred
  4. Log the timeout in `memory/incidents.jsonl`
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

### Dashboard Is Always Current (DUAL WRITE — MANDATORY)
- **TWO tasks.json files must stay in sync:**
  1. `~/.openclaw/workspace/tasks.json` — OpenClaw agents read/write here
  2. `~/JarvisMissionControl/backend/data/tasks.json` — Mission Control dashboard reads here
- **On EVERY task update** (status change, progress change, completion), write to BOTH files.
- **Monitor enforcement:** Every sweep, compare both files. If they differ, sync Mission Control from workspace (workspace is source of truth).
- New tasks must appear on the Task Board the moment they're requested.
- Progress updates must happen at every milestone (25→50→75→100).
- No task hits 100% without proof (commit SHA for code, Gmail ID for reports).
- Monitor verifies every 5 minutes; stale entries (>2h no update while running) trigger investigation + action.

**Sync command (run by Monitor if files differ):**
```bash
python3 -c "
import json, shutil
ws = json.load(open('$HOME/.openclaw/workspace/tasks.json'))
mc_path = '$HOME/JarvisMissionControl/backend/data/tasks.json'
mc = json.load(open(mc_path))
# Merge: workspace tasks into MC array format
ws_tasks = ws.get('tasks', {})
mc_ids = {t['id'] for t in mc}
for tid, tdata in ws_tasks.items():
    if tid not in mc_ids:
        mc.append({'id': tid, **tdata})
    else:
        for t in mc:
            if t['id'] == tid:
                t.update(tdata)
                break
with open(mc_path, 'w') as f:
    json.dump(mc, f, indent=2)
print(f'Synced {len(ws_tasks)} workspace tasks to Mission Control')
"
```

**Root cause lesson:** On 2026-03-25, the Anthropic research task showed 25% on the dashboard despite being 100% complete because only the workspace tasks.json was updated, not the Mission Control copy.

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

## Sweep Checklist (every 5 minutes — but Telegram ONLY once per hour)

### TELEGRAM THROTTLE (CHECK BEFORE EVERY SWEEP)
Before sending ANY Telegram message in this sweep, run:
```bash
python3 -c "
import json, time
d = json.load(open('memory/cron-state.json'))
last = d.get('last_telegram_sent', 0)
elapsed = int(time.time()) - last
if elapsed < 3600:
    print(f'SKIP_TELEGRAM (last sent {elapsed}s ago, next in {3600-elapsed}s)')
else:
    print('SEND_TELEGRAM_OK')
"
```
- If `SKIP_TELEGRAM`: do NOT send any Telegram message this sweep. Log findings to file only.
- If `SEND_TELEGRAM_OK`: send ONE combined hourly summary after all checks complete.
- **EXCEPTION:** Critical alerts (auth failure, PowerSpec offline with queued tasks) ALWAYS send immediately regardless of throttle.

### 0. Auth Pre-Flight (MANDATORY — runs first)
```bash
# 1. Check circuit breaker state (set by selfheal.sh every 10 min)
cat memory/cron-state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('AUTH_OK' if d.get('auth_healthy',True) else 'AUTH_BROKEN')"

# 2. If circuit breaker says healthy, verify with a live probe
gog gmail search "newer_than:1h" --max 1 --account ericfbrown1@gmail.com
gh auth status

# 3. Check fallback state
cat memory/auth-fallback-state.json
```
- If `gog` fails → do NOT run `gog auth add` (requires browser, fails in cron/agent). Instead:
  - Verify `memory/cron-state.json` has `auth_healthy: false` (selfheal sets this)
  - Verify `memory/auth-fallback-state.json` routes to Zapier MCP
  - If either is stale, update them manually and alert Eric via Telegram
- If `gh` fails → try `gh auth refresh` → if still fails, alert Eric
- **When in fallback mode:** Use Zapier MCP tools (`gmail_find_email`, `dropbox_upload_file`) instead of `gog` commands
- Log every auth event to `memory/incidents.jsonl`

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

### 4.5. Tailscale Health Check
```bash
tailscale status --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
state = d.get('BackendState', 'unknown')
self_online = d.get('Self', {}).get('Online', False)
peers = d.get('Peer', {})
online_peers = sum(1 for p in peers.values() if p.get('Online'))
total_peers = len(peers)
key_expiry = d.get('Self', {}).get('KeyExpiry', '')
print(f'State: {state} | Online: {self_online} | Peers: {online_peers}/{total_peers} | KeyExpiry: {key_expiry}')
"
```
**Checks:**
- `BackendState` must be `Running` — if not → alert Eric: "Open Tailscale app from menu bar"
- `Self.Online` must be `True` — if false → Tailscale connected but not routing traffic
- `remote-coder-main` must be in peers AND online — if offline → PowerSpec unreachable, escalate
- `KeyExpiry` within 7 days → warn Eric: "Tailscale key expires soon, re-authenticate"
- CLI path: if `which tailscale` = `/opt/homebrew/bin/tailscale` → warn: "Homebrew CLI conflicts with App Store app — run `brew uninstall tailscale`"

**If Tailscale is down:** All PowerSpec operations fail silently. This check catches it BEFORE Step 4 PowerSpec ping fails.

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

### 11. 4-Phase Workflow Compliance (MANDATORY)

Every running task must follow: **Understand → Plan → Implement → Verify** (see PIPELINE.md).

**Check for each running task:**
1. **Phase tracking:** Does `tasks.json` include a `phase` field? If missing → add it.
2. **Phase skipping:** Did an agent jump from Understand straight to Implement (skipping Plan)? → Flag as incident, pause task, notify Eric.
3. **Verify phase exists:** Is there a verification step defined? If task has no `successCriteria` in tasks.json → flag as incomplete dispatch.
4. **Verify actually ran:** Did the task reach Phase 4 (Verify) before being marked 100%? If `status === "completed"` but no test/review evidence → reject completion, send back to Verify.

**Phase compliance rules:**
- Code tasks: Must have PLAN.md before Coder starts. Must have test results before 100%.
- Research tasks: Must have search strategy before executing. Must cross-check sources before delivering.
- Report tasks: Must have outline before writing. Must verify deliverable sent before 100%.
- Error diagnosis: Must understand context before proposing fix. Must verify fix works before closing.

**Enforcement actions:**
- Missing phase → log to `memory/incidents.jsonl` with `error_category: "phase_skip"`
- Repeated phase skips (>2 in same task) → escalate to Eric
- Agent that consistently skips phases → flag in Librarian's next review

### 12. Status Report — SIZE BOUNDED (max 500 chars to Telegram)

**Healthy sweep:** `✅ All green [HH:MM]` (< 30 chars)
**Degraded sweep:** One line per failing check, max 5 lines:
```
❌ Auth: gog expired, switched to Zapier
❌ PowerSpec: offline, 3 retries failed
✅ 4/6 other checks passed
```

**RULES:**
- NEVER exceed 500 chars in a Telegram message
- If detail needed → write full report to `memory/monitor/sweep-YYYY-MM-DDTHH.md` and link it
- If message would exceed limit → truncate to summary + file link
- **Maximum notification frequency: ONCE PER HOUR for non-critical messages**
- Before sending any non-critical Telegram message, check `memory/cron-state.json` → `last_telegram_sent`. If <60 minutes ago, SKIP (write to log only).
- **Failures/critical alerts: send IMMEDIATELY** (bypass the hourly limit)

**Notification tiers:**
| Tier | When to Send | Frequency |
|------|-------------|-----------|
| CRITICAL | Auth failure, PowerSpec offline with queued tasks, dashboard mismatch | Immediately (no delay) |
| HOURLY | Healthy sweep summary, task milestone batches, system status | Once per hour max |
| SILENT | Routine healthy sweeps with no changes | Log only, no Telegram |

**Hourly report includes (batched):**
- System health summary (one line)
- Task milestone changes since last report: `📊 [TaskName]: 25% → 75%`
- Any warnings (non-critical) accumulated since last message
- Tailscale/PowerSpec status if changed

**After sending, update:**
```bash
python3 -c "
import json, time
with open('memory/cron-state.json') as f: d = json.load(f)
d['last_telegram_sent'] = int(time.time())
with open('memory/cron-state.json', 'w') as f: json.dump(d, f)
"
```

### 12. Dispatch Verification Check
- For every running task in tasks.json, verify a `verificationCmd` field exists
- Missing verification = incident → flag to Jarvis: "Task X has no verification command"
- Reference: DISPATCH_TEMPLATE.md — every dispatch must include verification criteria

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
