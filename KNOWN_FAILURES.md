# KNOWN_FAILURES.md — Agent Failure Patterns & Solutions

This file documents known failure patterns agents encounter, with proven solutions.
All agents should consult this before attempting workarounds.

---

## 🔴 Coder: Import Errors After Writing Code
**Pattern:** Coder writes new modules but doesn't verify imports resolve. Quality/Tester catches it → re-dispatch.
**Solution:** Run `python3 -c "import <module>"` for every new/modified Python file before marking task complete. Check `requirements.txt` includes all new dependencies.
**Frequency:** ~25% of Coder tasks
**Added:** 2026-03-11

## 🔴 Subagent Timeout (600s)
**Pattern:** Complex tasks (large codebases, multi-file changes) exceed the 600s timeout.
**Solution:** Write CHECKPOINT.md at each major step. If timeout occurs, Jarvis can resume from last checkpoint. Break large tasks into sub-tasks of <300s each.
**Frequency:** ~10% of complex tasks
**Added:** 2026-03-11

## 🔴 Gmail/Google OAuth Token Expiry
**Pattern:** `gog` CLI returns "invalid_grant" or "Token expired or revoked." All Google services (Gmail, Drive, Sheets, Calendar) stop working.
**Solution:** Run `gog auth login --account ericfbrown1@gmail.com --force-consent` locally (requires browser). Cannot be done remotely.
**Workaround:** Use Telegram for updates, Dropbox for file sharing.
**Frequency:** Happened Feb 26, Mar 8-10 2026
**Added:** 2026-03-11

## 🟡 Docker Not Installed on MacBook Pro
**Pattern:** `docker build` and `docker-compose up` fail because Docker Desktop is not installed.
**Solution:** `brew install --cask docker`, then launch Docker Desktop from Applications.
**Impact:** Cannot verify container builds locally until installed.
**Added:** 2026-03-11

## 🟡 Planner Missing Edge Cases
**Pattern:** Plans don't account for error handling, rate limits, auth expiry, null inputs. These surface during coding.
**Solution:** Planner now uses Edge Case Checklist (see PLAN.md template). GPT 5.4 cross-review specifically checks for edge cases.
**Frequency:** ~15% of plans
**Added:** 2026-03-11

## 🟡 Large File Context Overflow
**Pattern:** Reading large files (>100K chars) causes context to fill, leading to truncated responses or missed details.
**Solution:** Use `offset` and `limit` parameters for `read`. Process large files in chunks. For analysis, extract key sections rather than loading entire files.
**Frequency:** Occasional
**Added:** 2026-03-11

## 🟢 Dropbox Token Expiry
**Pattern:** Dropbox API token expires, `dropbox-cli.py` stops working.
**Solution:** Refresh at dropbox.com/developers. Eric's personal Dropbox is READ-ONLY — never modify.
**Last occurrence:** Feb 26, 2026
**Added:** 2026-03-11

---

_Updated by Jarvis. Agents: consult this file when encountering errors before attempting novel fixes._
