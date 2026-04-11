# OpenClaw System Audit Report
**Date:** April 10, 2026 — 21:41 PDT  
**Auditor:** Jarvis (acting as External Auditor — auditor agent not in spawn allowlist; flagged as P2 action item)  
**Reviewed by:** Grok 4.20 (adversarial cross-check on findings)  
**Scope:** Email sending, PPT creation, Dropbox R/W, config files, workspace .md files, Librarian findings

---

## Executive Summary

| # | Finding | Severity |
|---|---------|----------|
| 1 | `gog gmail send --attach` silently succeeds with missing/ephemeral files — no native validation | 🔴 P1 |
| 2 | PPT files generated to ephemeral paths — no durable write protocol enforced | 🔴 P1 |
| 3 | Auditor agent not in main agent's `subagents.allowAgents` — cannot be spawned autonomously | 🟡 P2 |
| 4 | PIPELINE.md references Auditor model as "Sonnet 4.6" but config now set to grok-4.20 — stale | 🟡 P2 |
| 5 | Himalaya skill missing — email fallback path not documented | 🟡 P2 |
| 6 | Google OAuth circuit breaker has triggered 3 times in 7 days — token stability fragile | 🟡 P2 |
| 7 | Dropbox access token expired at audit time — auto-refresh working but token_expiry not proactively refreshed | 🟢 P3 |
| 8 | Librarian indexer bug — `title` field not rendered in index.md | 🟢 P3 |
| 9 | DELEGATION.md references `~/.claude/projects/C--Users-ericf/memory/` path — likely stale (PowerSpec path) | 🟡 P2 |

---

## 1. Email Sending — Current State

### Toolchain
- **Primary:** `gog gmail send` (OAuth via macOS Keychain)
- **Fallback:** Zapier MCP `zapier.gmail_send_email`
- **Auth:** Google OAuth, re-issued 2026-04-09 after token expiry

### ✅ What's Working
- `gog gmail send` with `--body` (plain text, no attachment) works reliably — confirmed by test email at 21:34 PDT today (message_id: 19d7ad14d836dcbe)
- Gmail auth healthy: `gog gmail search "newer_than:2h"` returned results immediately
- Zapier MCP fallback available (20 tools loaded per TOOLS.md)
- CC rule enforced: ericfbrown1@gmail.com always CC'd

### 🔴 P1 — `gog gmail send --attach` phantom success bug (INC-20260409-128)
**Status: Known bug, no fix from gog CLI vendor. Workaround required.**

The `--attach` flag returns a valid `message_id` even when:
- The file does not exist at the specified path
- The file is zero bytes
- The path is a temp/session path that was cleaned up

**Required workaround (not yet enforced as a standing protocol):**
```bash
# Step 1: Pre-flight check
ls -la /path/to/file.pptx && [ -s /path/to/file.pptx ] || exit 1
# Step 2: Send
gog gmail send --to ... --attach /path/to/file.pptx
# Step 3: Post-confirm
gog gmail search "subject:YourSubject newer_than:5m" --max 1
```
**Action required:** Codify this as a mandatory 3-step delivery protocol in AGENTS.md and any skill that sends attachments.

### 🟡 P2 — Google OAuth triggering circuit breaker 3x in 7 days
- Apr 3, Apr 4, Apr 10 all show `auth_healthy=false` circuit breaker events in incidents.jsonl
- Root cause unclear — could be token revocation, Keychain corruption, or OAuth app issue
- Each time resolved by re-auth with `--force-consent`
- **Recommended:** Investigate whether OAuth app is still in "Testing" mode (7-day token expiry applies to testing apps). If so, publish to Production in Google Cloud Console — permanent fix per the Google OAuth lesson in AGENTS.md.

### 🟡 P2 — Himalaya skill missing
- `/Users/ericbrown/.openclaw/workspace/skills/himalaya/SKILL.md` does not exist
- TOOLS.md does not document an IMAP/SMTP fallback path
- If gog AND Zapier MCP both fail, there is no third email option
- **Recommended:** Install himalaya skill from ClawhHub or document the Zapier fallback explicitly as the sole alternative in skills/gog/SKILL.md

---

## 2. PPT/PPTX Creation — Current State

### Toolchain
- **Library:** `python-pptx` — ✅ confirmed installed (`import pptx` OK)
- **Generator:** Ad-hoc Python scripts written per-request (no reusable skill)
- **Output path:** `~/Documents/` (when correctly specified)

### ✅ What's Working
- `python-pptx` installed and functional
- Generation script approach works (12-slide deck created and emailed today)
- File saved correctly to `~/Documents/ai-best-practices-cohesity.pptx` (45,196 bytes)

### 🔴 P1 — No durable file write protocol
**The Apr 8 incident root cause:** File generated to an ephemeral path, session ended, file gone. No backup. No verification.

Current state: there is **no enforced protocol** that requires:
1. Writing generated files to `~/Documents/` (not `/tmp/` or session scratch)
2. Verifying file exists + non-zero size before attempting send
3. Uploading to Dropbox `/Jarvis Reports/` as backup before email

**Action required:** Add the following as a standing rule in AGENTS.md under "File Delivery Protocol":
```
For any generated file (PPTX, DOCX, PDF):
1. Always write to ~/Documents/<filename> (never /tmp or session paths)
2. Verify: ls -la + file size > 0 before send
3. Upload to Dropbox /Jarvis Reports/ as backup
4. Send email with attachment
5. Confirm: gog gmail search to verify receipt
```

### 🟡 P2 — No reusable PPT skill
- Every PPTX request requires writing a generation script from scratch
- Risk of inconsistent slide layouts, color schemes, content structure
- **Recommended:** Create a `pptx-generator` skill with Eric's standard template (Cohesity colors, slide layouts) and a reusable Python class

---

## 3. Dropbox Read/Write — Current State

### ✅ What's Working
- `dropbox-cli.py` — self-contained, reads exclusively from `.dropbox_auth.json` (chmod 600, no inline credentials)
- Refresh token is permanent (never expires unless app revoked)
- Auto-refresh on every API call — transparent to callers
- File permissions correct: `-rw------- (600)`
- Status check confirms: App Key ✅, App Secret ✅, Refresh Token ✅

### 🟢 P3 — Access token expired at audit time
- `Token Status: 🔄 Expired (will auto-refresh)` — this is **expected and healthy** behavior
- The CLI will transparently refresh before next operation
- Not a bug, just the normal 4-hour expiry cycle

### ✅ Architecture quality: Good
- No subprocess dependencies (fixed in INC-20260409-127)
- Single source of truth for credentials
- Proper separation: `.dropbox_auth.json` for secrets, `dropbox-cli.py` for logic

### ⚠️ Gap: No smoke test in cron
- `dropbox-cli.py status` is not included in the daily smoke test suite
- A silent Dropbox failure would not be caught until a delivery fails
- **Recommended (P3):** Add `python3 ~/.openclaw/workspace/dropbox-cli.py list "/Jarvis Reports/" --max 1` to the daily smoke test

---

## 4. Config & Skills — Findings

### openclaw.json
| Item | Status | Note |
|------|--------|------|
| Main agent model | ✅ opus-4-6 primary | Correct |
| All subagents | ✅ sonnet-4-6 primary | Correct |
| Auditor model | ✅ grok-4.20 primary | Updated tonight |
| plugins: 51 loaded, 0 errors | ✅ Healthy | |
| Gateway bind: 0.0.0.0 | ⚠️ LAN-exposed | Rate limiting in place (Apr 9 audit); loopback+Tailscale Serve recommended long-term |
| Stale gateway plist | ✅ Removed | Done tonight |

### 🟡 P2 — Auditor not in main agent's spawn allowlist
```json
"subagents": {
  "allowAgents": ["researcher", "planner", "coder", "quality", "monitor", "conductor"]
}
```
`auditor` is absent. Cannot be spawned via `sessions_spawn` from main agent. This audit had to be run manually by Jarvis acting as auditor. 
**Fix:** Add `"auditor"` to `allowAgents` in main agent config.

### 🟡 P2 — PIPELINE.md model table stale
- PIPELINE.md lists "External Auditor: Sonnet 4.6" — now incorrect after tonight's switch to grok-4.20
- **Fix:** Update PIPELINE.md model tiering table to reflect grok-4.20 for auditor

### Skills inventory
| Skill | Status |
|-------|--------|
| gog (Gmail/Sheets/Drive) | ✅ Present, functional |
| himalaya (IMAP email) | ❌ Missing — file not found |
| firecrawl | ✅ Present |
| coding-agent | ✅ Present |
| librarian | ✅ Present |
| auditor | ✅ Present |
| monitor | ✅ Present |

---

## 5. Workspace .md Files — Findings

| File | Status | Issue |
|------|--------|-------|
| AGENTS.md | ✅ Healthy (4.1KB) | Within size limit |
| SOUL.md | ✅ Good | No issues |
| USER.md | ✅ Current | Up to date |
| MEMORY.md | ✅ Current | Dropbox, OAuth, voice calls all documented |
| DELEGATION.md | ⚠️ Stale path | References `~/.claude/projects/C--Users-ericf/memory/` — this appears to be an old PowerSpec/Claude Code path. If Planner/Coder agents are using this path to look for memory files and it doesn't exist, the "Learn First" loop silently fails. |
| PIPELINE.md | ⚠️ Stale model | Auditor listed as Sonnet 4.6 |
| PIPELINE.md | ⚠️ References GPT-5.4 | "Planner: GPT-5.4 cross-review" in Phase 2 description — DELEGATION.md says Grok 4.20 Beta. Inconsistent. |

### 🟡 P2 — DELEGATION.md memory path likely stale
```
Read `~/.claude/projects/C--Users-ericf/memory/MEMORY.md`
```
This path (`~/.claude/projects/C--Users-ericf/`) is the Claude Code projects directory from an older setup. If this doesn't exist, the "Learn First" and "Learn Before Code" rules in DELEGATION.md silently fail — agents skip memory reads and plan/code in a vacuum.

**Fix:** 
1. Check if `~/.claude/projects/C--Users-ericf/memory/` exists
2. If not, update DELEGATION.md to point to `~/.openclaw/workspace/memory/` and `~/.openclaw/workspace/ClawEvolveRepo/`

---

## 6. Librarian Findings — System Stability Assessment

### Recent wins (Apr 9-10, all resolved)
| ID | Issue | Pattern |
|----|-------|---------|
| INC-20260409-126 | Exec preflight silently blocked all cron jobs using `cd &&` | Silent failure from platform update |
| INC-20260409-127 | Dropbox token refresh fragile subprocess dependency | Brittle external dependency |
| INC-20260409-128 | gog `--attach` phantom success with missing file | Tool doesn't validate inputs |

### Pattern Analysis
**Recurring theme: Silent failures.** All 3 recent incidents share the same failure mode — a tool or pipeline reports success while actually doing nothing. This is the same pattern as the FinancialReportApp incident (INC-20260328). The system has an endemic "phantom success" problem.

**Root causes by category:**
- Platform changes breaking existing patterns (exec preflight) — no automated regression test catches these
- External tool bugs (gog `--attach`) — no workaround enforcement
- Fragile architecture (subprocess dependencies) — fixed but recurrence risk if other scripts follow the same pattern

**Stability trend:** Improving. The Apr 9 audit resolved all active issues. No open P1 incidents. But the frequency of circuit breaker triggers (3x in 7 days for OAuth) warrants investigation.

### 🟢 P3 — Librarian indexer bug
- `librarian.py --index` does not render `title` field in `index.md`
- The full JSON files are correct and searchable
- Impact: low (prior-art lookup still works via JSON files)
- Fix: Update `librarian.py` to include title in index entry

---

## Action Items (Prioritized)

### 🔴 P1 — Fix Now
| # | Action | File to Update |
|---|--------|----------------|
| 1.1 | Add mandatory 3-step file delivery protocol (pre-check → send → confirm) as standing rule | AGENTS.md |
| 1.2 | Add file persistence rule: all generated files written to `~/Documents/` AND backed up to Dropbox `/Jarvis Reports/` before email send | AGENTS.md |

### 🟡 P2 — Fix This Week
| # | Action | File to Update |
|---|--------|----------------|
| 2.1 | Add `auditor` to main agent `subagents.allowAgents` in openclaw.json | openclaw.json |
| 2.2 | Update PIPELINE.md model tiering table: Auditor = grok-4.20 (not Sonnet 4.6) | PIPELINE.md |
| 2.3 | Fix PIPELINE.md Phase 2 — references GPT-5.4 cross-review; should be Grok 4.20 Beta | PIPELINE.md |
| 2.4 | Verify DELEGATION.md memory paths exist; update to correct workspace paths | DELEGATION.md |
| 2.5 | Investigate Google OAuth repeated circuit breaker (check if OAuth app is in Testing vs Production mode) | Google Cloud Console |
| 2.6 | Install himalaya skill or explicitly document Zapier MCP as email fallback in gog SKILL.md | skills/gog/SKILL.md |

### 🟢 P3 — Fix When Time Allows
| # | Action | File to Update |
|---|--------|----------------|
| 3.1 | Add `dropbox-cli.py status` to daily smoke test | cron job payload |
| 3.2 | Fix `librarian.py --index` to render title field in index.md | skills/librarian/librarian.py |
| 3.3 | Create reusable `pptx-generator` skill with Eric's standard Cohesity template | skills/pptx-generator/ |
| 3.4 | Long-term: switch gateway bind from 0.0.0.0 to loopback + Tailscale Serve for remote access | openclaw.json |

---

## Live Health Check Results (as of audit)

| System | Status |
|--------|--------|
| python-pptx | ✅ Installed |
| .dropbox_auth.json | ✅ Exists, chmod 600, 1535 bytes |
| Dropbox CLI | ✅ Auth healthy, auto-refresh working |
| Gmail (gog) | ✅ OAuth healthy, search returning results |
| Gateway | ✅ Running, Telegram bot online |
| Stale plist | ✅ Removed |

---

*Report written by Jarvis acting as External Auditor — April 10, 2026 21:41 PDT*  
*Note: Auditor agent was not spawnable (not in allowAgents list — see P2 action item 2.1)*
