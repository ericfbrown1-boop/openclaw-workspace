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

## 🔴 Railway: railway.json startCommand conflicts with Dockerfile CMD
**Pattern:** Using both `railway.json` `startCommand` AND `Dockerfile` `CMD` causes unpredictable behavior. Railway Agent often creates malformed railway.json files.
**Solution:** Use ONLY the Dockerfile CMD for startup commands. Remove `startCommand` from railway.json entirely. If railway.json exists, it should contain ONLY build settings (builder, buildCommand). Use shell form for variable expansion: `CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
**Frequency:** ContractAnalyzer Mar 16, 2026 — 4 commits fighting this conflict
**Added:** 2026-03-17

## 🟡 Railway: pgvector CREATE EXTENSION must precede create_all
**Pattern:** `InFailedSQLTransactionError` at startup when using pgvector with SQLAlchemy. `CREATE EXTENSION vector` and `Base.metadata.create_all()` in the same transaction causes failure.
**Solution:** Run `CREATE EXTENSION IF NOT EXISTS vector` in a separate transaction BEFORE `Base.metadata.create_all()`. Commit the extension creation first, then run create_all.
**Frequency:** ContractAnalyzer Mar 16, 2026
**Added:** 2026-03-17

## 🟡 Railway: Celery broker not ready at startup
**Pattern:** Celery worker crashes on startup because Redis broker isn't ready yet. Railway starts all services in parallel.
**Solution:** Set `broker_connection_retry_on_startup=True` in Celery config. This makes the worker wait for the broker instead of crashing.
**Frequency:** ContractAnalyzer Mar 16, 2026
**Added:** 2026-03-17

## 🟡 Railway: PORT variable expansion fails in exec form
**Pattern:** `Error: Invalid value for '--port': '$PORT' is not a valid integer` — Docker exec form doesn't expand variables.
**Solution:** Use shell form CMD: `CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]` NOT exec form: `CMD ["uvicorn", "--port", "$PORT"]`
**Frequency:** ContractAnalyzer Mar 16, 2026 — 3 commits fixing this
**Added:** 2026-03-17

## 🟡 Auth cascade: Multiple credentials expire simultaneously
**Pattern:** gog CLI (Google OAuth), gh CLI (GitHub), himalaya (IMAP) all expire at once. Briefings fail repeatedly with no fallback. Gateway enters restart loop from LLM timeouts.
**Solution:** Pre-check auth health before credential-dependent work: `gog gmail search "newer_than:1h" --max 1` and `gh auth status`. If failing, use fallback paths: Zapier MCP for email, Telegram for notifications. Do NOT retry the same broken auth path.
**Frequency:** Mar 13, 2026 — 7 failed briefing attempts
**Added:** 2026-03-17

## 🟡 Cron storm: Same job runs multiple times
**Pattern:** Same cron job (e.g., daily briefing) triggers multiple times due to heartbeat retriggers or gateway restarts. Each run spawns a new isolated session, wasting tokens.
**Solution:** Check `memory/cron-state.json` for last successful run before executing. If same cron ID completed within the past 4 hours, skip with HEARTBEAT_OK.
**Frequency:** Mar 13, 2026 — briefing ran 7 times
**Added:** 2026-03-17
