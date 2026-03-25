# OpenClaw Stability Fix Plan — Auth & API Credit Monitoring

**Created:** 2026-03-25
**Status:** Ready for implementation
**Priority:** Critical (auth stability), High (API credit monitoring)

---

## Problem 1: Continuous Google OAuth Reauth

### Root Cause Analysis

The `gog` CLI stores OAuth tokens in the macOS Keychain. When a token expires or is revoked, the CLI keeps trying the stale cached token instead of refreshing. The fix requires manual browser interaction (delete keychain entry + `gog auth add --force-consent`). The system has several detection mechanisms (Monitor sweep, selfheal, daily smoketest) but **no automated fix** — they all detect the problem and then either alert Eric or attempt the same broken `gog auth add` which fails without a browser.

### Specific gaps found in the code

1. **`selfheal.sh` (line 38-53)**: Checks gateway process and RPC health but does **zero Google OAuth checks**. It only handles LLM timeouts and gateway restarts.

2. **`monitor/SKILL.md` (line 75)**: Says "if gog fails → immediately run `gog auth add --force-consent`" but this **requires a browser** and will silently fail in a cron/agent context.

3. **`KNOWN_FAILURES.md` (line 23)**: Documents the pattern but solution says "Cannot be done remotely" — yet the system keeps trying.

4. **No proactive token refresh**: The gog CLI relies on Google's refresh token, but there's no code that explicitly calls a token refresh before expiry.

5. **Cron storm amplification** (`KNOWN_FAILURES.md` line 87): When auth breaks, cron jobs retry 7+ times, each spawning isolated sessions, wasting tokens AND compounding the problem.

### Proposed Fixes — Auth Stability

#### Fix 1A: Add Google OAuth health check to `selfheal.sh`
- Add a new section (between step 2 and step 3) that runs `gog gmail search "newer_than:1d" --max 1`
- On failure: immediately log to incidents.jsonl, switch all agents to Zapier MCP fallback mode, and send Telegram alert to Eric with the exact fix command
- On success: ensure fallback mode is disabled
- **File:** `scripts/openclaw_selfheal.sh`

#### Fix 1B: Create a token refresh wrapper script `scripts/gog_token_refresh.sh`
- Attempts `gog auth refresh` (if the CLI supports it) before the token fully expires
- Runs via LaunchAgent every 3 hours (well within the token expiry window)
- If refresh fails: deletes stale keychain entry, logs the event, sends Telegram notification
- Does NOT attempt browser auth (that's manual only)
- **File:** new `scripts/gog_token_refresh.sh`

#### Fix 1C: Add circuit breaker to prevent cron storms
- Enhance `memory/cron-state.json` with an `auth_healthy` boolean flag
- All cron jobs that depend on Google OAuth check this flag FIRST
- If `auth_healthy === false`, skip with `HEARTBEAT_OK` instead of retrying
- `selfheal.sh` sets the flag based on actual OAuth probe results
- **Files:** `scripts/openclaw_selfheal.sh`, `AGENTS.md` (update cron deduplication section)

#### Fix 1D: Add auto-fallback to Zapier MCP in Monitor sweep
- When OAuth fails and browser reauth isn't possible, Monitor should automatically route Gmail/Sheets operations through Zapier MCP
- Create a `memory/auth-fallback-state.json` file tracking which services are in fallback mode
- Agents check this state before choosing gog vs Zapier
- **Files:** `skills/monitor/SKILL.md`, new `memory/auth-fallback-state.json`

---

## Problem 2: No API Credit/Usage Warnings

### Root Cause Analysis

`USER.md` lines 77-79 say "Do not exceed monthly plan limits; pause and confirm if spend could exceed them" and "Always notify Eric if a task would require additional payment." But there is **zero code** implementing this. The system relies entirely on agents reading USER.md and manually estimating costs — which they don't do.

The `PIPELINE.md` Model Tiering Strategy (line 57-70) shows cost awareness at the model selection level, but no actual tracking or alerting.

### Proposed Fixes — API Credit Monitoring

#### Fix 2A: Create `scripts/api_usage_monitor.py`
- Query the Anthropic API usage endpoint (or parse auth-profiles.json usage stats) to get current spend
- Compare against configurable thresholds (e.g., 50%, 75%, 90% of monthly budget)
- On threshold breach: send Telegram alert + update `memory/api-usage-state.json`
- Run via selfheal.sh (every 10 min) or as its own LaunchAgent (every hour)
- **File:** new `scripts/api_usage_monitor.py`

#### Fix 2B: Add usage tracking to `auth-profiles.json` processing in selfheal
- The selfheal script already reads `auth-profiles.json` (line 101-123) to clear cooldowns
- Extend it to also read `usageStats` and compute daily/monthly token usage
- Log usage snapshots to `logs/api_usage.jsonl`
- **File:** `scripts/openclaw_selfheal.sh`

#### Fix 2C: Add cost gate to PIPELINE.md and AGENTS.md
- Before any Opus 4.6 task, agents must check `memory/api-usage-state.json`
- If usage > 75% of budget: downgrade to Sonnet 4.6 for all non-critical tasks
- If usage > 90%: pause non-essential work and alert Eric
- **Files:** `PIPELINE.md`, `AGENTS.md`

#### Fix 2D: Add API usage section to daily smoketest
- New section 6.5 in `daily_smoketest.sh` between LLM Provider Health and Agent Configuration
- Reports: daily token count, estimated cost, monthly projection, budget remaining
- Flags warnings at 75%/90% thresholds
- **File:** `scripts/daily_smoketest.sh`

#### Fix 2E: Add credit check to daily briefing email
- Include a "Budget Status" line in the 6 AM daily briefing
- Format: "API Budget: $X spent / $Y limit (Z% used, N days remaining)"
- **File:** Update daily briefing cron payload to include budget data

---

## Implementation Order

| Step | Fix | Risk | Effort |
|------|-----|------|--------|
| 1 | 1C — Circuit breaker (stops the bleeding) | Low | Small |
| 2 | 1A — OAuth check in selfheal | Low | Small |
| 3 | 1D — Auto-fallback to Zapier MCP | Low | Medium |
| 4 | 1B — Token refresh wrapper | Low | Small |
| 5 | 2A — API usage monitor script | Low | Medium |
| 6 | 2B — Usage tracking in selfheal | Low | Small |
| 7 | 2C — Cost gate in pipeline docs | Low | Small |
| 8 | 2D — Usage in daily smoketest | Low | Small |
| 9 | 2E — Credit check in briefing | Low | Small |

## Files to Modify
1. `scripts/openclaw_selfheal.sh` — Add OAuth check + usage tracking
2. `scripts/daily_smoketest.sh` — Add API usage section
3. `skills/monitor/SKILL.md` — Add auto-fallback instructions
4. `AGENTS.md` — Update cron deduplication with auth circuit breaker
5. `PIPELINE.md` — Add cost gate rules
6. `KNOWN_FAILURES.md` — Update with new prevention measures

## New Files to Create
1. `scripts/gog_token_refresh.sh` — Proactive token refresh
2. `scripts/api_usage_monitor.py` — API spend tracking + alerts
3. `memory/auth-fallback-state.json` — Fallback mode tracking
4. `memory/api-usage-state.json` — Budget/usage tracking

---

## How to Implement

On the Mac, start Claude Code in the workspace:
```bash
cd ~/.openclaw/workspace
claude
```

Then tell Claude:
```
Read plans/stability-fix-plan.md and implement fixes 1C, 1A, 1D, 1B in order (auth stability).
Then implement fixes 2A through 2E (API credit monitoring).
Reference the 8 coding agents in DELEGATION.md. Test each change before moving to the next.
```
