---
name: rca-agent
description: >
  Dual-model adversarial RCA protocol. Spawns RCA Agent (GPT-5.4) + Auditor Agent (Grok 4.20) 
  in parallel to diagnose failures. The two agents debate, research independently, then produce 
  a joint fix plan executed autonomously. Use whenever something breaks — no Eric involvement required.
---

# RCA Agent Skill — Dual-Model Adversarial Root Cause Analysis

## When to Invoke

Trigger this skill AUTOMATICALLY (without waiting for Eric) when ANY of the following occur:
- Gateway restart or disconnect
- Web UI stall or unresponsiveness
- Any subagent failure with SIGTERM or gateway closed errors
- Session lock contention or 10s timeout in logs
- Any tool returning an error 2+ times in a row
- Email/report delivery failure
- SSH/Tailscale connectivity loss
- Docker container crash
- Any OpenClaw packaging/module error

Do NOT wait for Eric to notice or report. Launch the dual-RCA immediately and autonomously.

---

## 🪵 MANDATORY: Full Log Collection (Phase 0 — Before Any Diagnosis)

**BOTH agents must review ALL available logs before forming any hypothesis.**
This is non-negotiable. Skipping logs = invalid RCA.

### Log Collection Commands (run at RCA start, share output with both agents)

```bash
# 1. Gateway log — last 200 lines (most important)
tail -200 ~/.openclaw/logs/gateway.log 2>/dev/null

# 2. Gateway errors and warnings only (non-routine)
grep -i "error\|warn\|disconnect\|close\|1012\|1011\|timeout\|lock\|SIGTERM\|SIGKILL\|fail\|crash" \
  ~/.openclaw/logs/gateway.log 2>/dev/null | tail -100

# 3. OpenClaw system log
tail -100 ~/.openclaw/logs/openclaw.log 2>/dev/null || \
  log show --predicate 'subsystem == "ai.openclaw"' --last 1h 2>/dev/null | tail -100

# 4. Gateway status
openclaw status 2>&1

# 5. Session store state
openclaw sessions cleanup --all-agents --dry-run 2>&1 | head -50

# 6. Active tasks and issues
openclaw tasks list 2>&1 | head -40
openclaw tasks maintenance 2>&1 | head -20

# 7. JarvisMissionControl logs (if MC issue)
pm2 logs --lines 100 jarvis-mission-control 2>/dev/null | tail -100
cat ~/JarvisMissionControl/.next/server-logs.txt 2>/dev/null | tail -50
curl -s http://localhost:3000/api/health 2>/dev/null

# 8. Docker container logs (if container issue)
ssh "Eric Brown@100.81.21.114" "docker ps -a && docker logs --tail 50 \$(docker ps -q | head -1)" 2>/dev/null

# 9. macOS system log for crashes
log show --predicate 'eventMessage contains "openclaw" OR eventMessage contains "node"' \
  --last 30m 2>/dev/null | tail -50

# 10. Tailscale status
/usr/local/bin/tailscale status 2>&1

# 11. Recent incidents for pattern matching
tail -20 ~/.openclaw/workspace/memory/incidents.jsonl 2>/dev/null

# 12. Today's memory file for context
cat ~/.openclaw/workspace/memory/$(date +%Y-%m-%d).md 2>/dev/null | tail -50
```

### What to look for in logs:
| Pattern | Likely Cause |
|---------|-------------|
| `sessions.list` every <3s | Client polling loop — session bloat |
| `lock timeout` / `EWOULDBLOCK` | sessions.json contention |
| `gateway closed (1012)` | Gateway restart mid-session |
| `SIGTERM` on subagent | Session timeout hit |
| `Cannot find module` | OpenClaw packaging bug |
| `ECONNREFUSED :18789` | Gateway not running |
| `ECONNREFUSED :3000` | MC not running |
| `UNAVAILABLE` on WebSocket | Gateway restart in progress |
| `401` / `auth` errors | API key issue |
| `ENOMEM` / `heap` | Memory pressure |

---

## The Protocol

### Phase 0: Log Collection (MANDATORY FIRST STEP)
Both agents collect and review ALL logs above before forming any hypothesis.
Paste log excerpts into the RCA file under "Raw Evidence."

### Phase 1: Parallel Independent Analysis

After log review, both agents independently form their diagnosis:

**Auditor Agent (Grok 4.20) — System Insider:**
- Diagnoses from logs, system state, OpenClaw internals
- Checks for known patterns in `memory/incidents.jsonl`
- Cross-references today's `memory/YYYY-MM-DD.md` for recent changes that might have triggered this
- Writes initial findings to `plans/rca-<incident-id>-<date>.md` under "Auditor Analysis"

**RCA Agent (GPT-5.4) — Independent Researcher:**
- Researches the exact error/symptom online:
  - GitHub issues (search: `site:github.com <exact error message>`)
  - Stack Overflow (search: `<exact error> site:stackoverflow.com`)
  - Official docs: https://docs.openclaw.ai (OpenClaw-specific), Node.js docs, Python docs
  - Recent blog posts and changelogs for the affected software version
  - CVE databases if security-related
- **Security rule:** NEVER access OpenClaw community forums, Discord, Moltbook, or Reddit for OpenClaw internals. Only docs.openclaw.ai.
- Challenges or confirms Auditor's findings with external evidence
- Writes findings to the same RCA file under "RCA Agent Analysis"

### Phase 2: Adversarial Debate

Main agent (Jarvis) reads both analyses:
- **If AGREE:** Document consensus, move to fix plan
- **If DISAGREE:** 
  - Document both hypotheses with supporting evidence
  - If safe to test both → test both, see which fix resolves it
  - If only one can be applied → pick the one with stronger log evidence
  - Document which theory won and why

### Phase 3: Joint Fix Plan

Fix plan requirements (NON-NEGOTIABLE):
1. **Fully autonomous** — no Eric approval needed unless: (a) costs real money, (b) sends external comms, (c) deletes Eric's files
2. **Verified** — every fix must include a test that PROVES it worked
3. **Prevention** — add monitoring/alerting/config so this can't happen silently again
4. **Documented** — write to RCA file under "Joint Fix Plan"

### Phase 4: Execute, Verify, Report

Main agent (Jarvis) executes:
1. Apply all fixes from Joint Fix Plan
2. Run verification tests — confirm with concrete output (not just "seems fine")
3. Update `memory/incidents.jsonl` as resolved
4. Notify Eric via Telegram:
   ```
   🔧 Auto-fix complete: <incident title>
   
   Root cause: <1 sentence>
   Fixed: <bullet list of fixes>
   Prevention: <bullet list of prevention added>
   Verified: <test results>
   
   Full RCA: plans/rca-<incident-id>-<date>.md
   ```

---

## RCA File Format

```markdown
# RCA: <incident title> — <date>

## Incident ID
INC-YYYYMMDD-NNN

## Trigger
[What triggered the RCA — automatic detection or Eric report]

## Symptoms
[Exact symptoms with timestamps from logs]

## Raw Evidence (Logs)
### Gateway Log Excerpt
[Relevant lines from gateway.log]

### System State at Time of Incident
[openclaw status output, session counts, task counts]

### Relevant Error Messages (exact)
[Copy-paste exact error strings — critical for web research]

## Auditor Agent Analysis (Grok 4.20)
[Findings from logs + internals + INCIDENTS.md pattern match]

## RCA Agent Analysis (GPT-5.4)
[Independent research findings with sources, counterpoints or agreement]

## Debate Summary
[What each agent said, points of agreement/disagreement, resolution]

## Root Cause (Agreed)
[Final root cause with evidence trail from logs → diagnosis]

## Contributing Factors
[Secondary causes that worsened the primary]

## Joint Fix Plan
### Immediate Fixes (applied now)
- [ ] Fix 1: <command> → <expected result>
- [ ] Fix 2: <command> → <expected result>

### Prevention (permanent)
- [ ] Config change: <what changed>
- [ ] Monitoring: <what was added>
- [ ] Cron/schedule: <what runs when>

### Verification Tests
- [ ] Test 1: <command> → <expected output that proves fix worked>
- [ ] Test 2: <command> → <expected output>

## Execution Log
[Timestamped record of what was actually done]

## Outcome
[Test results, current system state, confirmed resolved Y/N]

## Prevention Added
[Concrete list of what was added to prevent recurrence]

## Lessons Learned
[What to add to INCIDENTS.md, AGENTS.md, or skill files]
```

---

## Spawning the Dual-RCA

When Jarvis triggers this skill:

```python
# Collect all logs first, save to a temp file
log_bundle = exec("tail -200 ~/.openclaw/logs/gateway.log && openclaw status && openclaw tasks maintenance")

# Spawn both simultaneously with the log bundle in the brief
auditor_session = sessions_spawn(
    task=f"Auditor RCA for {incident_id}. Logs:\n{log_bundle}\n[full brief]",
    agentId="auditor"  # uses xai/grok-4.20
)

rca_session = sessions_spawn(
    task=f"RCA Agent for {incident_id}. Logs:\n{log_bundle}\n[full brief]",
    agentId="rca-agent"  # uses codex/gpt-5.4
)

# Wait for both to complete, then synthesize and execute fix
```

---

## Session Cleanup (Run Weekly — Prevents Lock Contention)

```bash
openclaw sessions cleanup --all-agents --enforce 2>&1
openclaw tasks maintenance --apply 2>&1
```

Add to weekly cron. Session bloat (>100 sessions) is a known cause of lock contention.

---

## Security Note
- NEVER access OpenClaw community forums, Discord, Moltbook, or Reddit for OpenClaw-specific internals
- For OpenClaw issues: use only https://docs.openclaw.ai
- For general tech (Node.js, Python, Docker, nginx): GitHub issues, Stack Overflow, official docs are fine
- When in doubt about a source: skip it and rely on logs + official docs
