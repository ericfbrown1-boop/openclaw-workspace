# KNOWN_FAILURES.md — Agent Failure Patterns & Solutions
> **L1:** 16 documented failure patterns with proven fixes. Covers: import errors, subagent timeouts, OAuth expiry, Docker issues, Railway config, auth cascades, cron storms, bot detection, PowerShell TLS.

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
**Solution:** Planner now uses Edge Case Checklist (see PLAN.md template). Grok 4.20 Beta adversarial review specifically checks for edge cases (replaced GPT 5.4 cross-review on 2026-03-27).
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

## 🟡 Context Window Exceeded on Batch URL Processing
**Pattern:** Passing multiple URLs (e.g., 17 Rubrik pages) to an agent in a single prompt overflows the context window. Agent truncates or fails silently.
**Solution:** Process URLs one at a time. Chunk large payloads into individual requests. Write intermediate results to file between chunks so a fresh session can resume.
**Frequency:** ProjectScraper first crawl, Mar 5, 2026
**Added:** 2026-03-25
**Reference:** references/Morning_Session_Recap_EricBrown.docx

## 🟡 Web Scraping: Bot Detection Triggers
**Pattern:** Rapid sequential HTTP requests to competitor sites (Rubrik, Commvault) trigger bot detection, returning 403/captcha instead of content.
**Solution:** Add 3-second delay between requests. Rotate user-agent strings. Use headless Playwright (not raw HTTP) for JavaScript-rendered pages. Avoid hitting the same domain more than once per 5 seconds.
**Frequency:** ProjectScraper Rubrik crawl, Mar 5, 2026
**Added:** 2026-03-25
**Reference:** references/Morning_Session_Recap_EricBrown.docx

## 🟡 runs.json is a failure log, not an audit trail
**Pattern:** Reading `~/.openclaw/subagents/runs.json` and seeing only `[error]` entries triggers "every subagent spawn has failed" misdiagnosis.
**Reality:** Successful runs are pruned on completion. The persisted entries are incidents worth keeping — use as a failure watchlist, not a full history. The openclaw gateway cleans up successful child sessions; only ones that errored stay in `runs.json` for forensics.
**Check instead:** Run outputs in `pipeline-outputs/<task-id>/`, `memory/pipeline-state.json` for recent pipelines, `~/.openclaw/agents/<agent>/sessions/` for per-session logs, and `~/.openclaw/tasks/runs.sqlite` for the full task-run history.
**Frequency:** Misread 2026-04-11 during full-pipeline smoke test.
**Added:** 2026-04-11

## 🔴 Jarvis one-turn CLI limit — main narrates but doesn't orchestrate
**Pattern:** `openclaw agent --agent main --message "..."` runs ONE CLI turn per invocation. Main's reply text narrates "dispatching to Auditor now" but `sessions_spawn` is not actually executed before the turn ends. Full Research→Plan→Audit→Code→Quality chains documented in DELEGATION.md don't actually run from a single dispatch.
**Root cause:** `/opt/homebrew/lib/node_modules/openclaw/dist/acp-cli-DsBOatVe.js` `handlePayload()` → `finishPrompt()` resolves the turn on `state === "final"` without processing pending tool calls. Upstream package file — patching it would break on next `openclaw update`.
**Solution:** Use the external orchestrator `~/openclaw-workspace/scripts/jarvis_pipeline.py` which drives each stage via `openclaw agent --agent <id>` sequentially, capturing outputs and feeding them forward. Resumable via `--resume`. Mandatory Quality gate. Dual-writes task status to both tasks.json stores.
**How to recognize:** You dispatch to main, reply text says "dispatching to X next", no subsequent subagent run appears in `~/.openclaw/subagents/runs.json` or `pipeline-outputs/<task-id>/`, and nothing new lands on disk within 60s of main's turn ending.
**Added:** 2026-04-11

## 🟠 Planner writes unauthorized helper scripts + edits tasks.json — FIXED 2026-04-11
**Pattern:** When given a complex task description with specific verification requirements, Planner uses its `write` tool to pre-create helper scripts (e.g., `verify_powerspec_smoke.sh`) in `~/openclaw-workspace/scripts/` AND modifies `~/openclaw-workspace/tasks.json` to point the task's `verificationCmd` at the script. This violates Planner's scope — Planner's job is to emit PLAN.md only.
**Root cause:** Planner's system prompt encourages "be proactive" and "reduce Coder's burden". With `write` tool allowed (per openclaw.json), Planner interprets complex verification needs as "I should build the verification harness myself". No explicit scope boundary.
**Fix applied:** (1) Removed `write` from Planner's tools allowlist in `~/.openclaw/openclaw.json` — moved to `deny` list. (2) Added explicit `## Scope Boundary` rule to `workspace-planner/RULES.md`: "NEVER modify any file outside the target project's PLAN.md and PROJECT_CONTEXT.md."
**Frequency:** Observed 2026-04-11 during Option C smoke test.
**Added:** 2026-04-11

## 🟡 PowerSpec openclaw node host disconnects after ~50 min idle — FIXED 2026-04-11
**Pattern:** `openclaw nodes list` on the Mac shows PowerSpec as paired, but `exec` tool calls to `host=PowerSpec` return "node not connected". The node host scheduled task is still "Ready" but the websocket to the Mac gateway has dropped.
**Root cause:** The node host establishes an outbound WebSocket to the Mac gateway on startup, but the connection has no heartbeat / keepalive. Idle periods >50 min cause the gateway side to drop the connection; the node doesn't reconnect automatically.
**Fix applied:** `_powerspec_ensure_node_alive()` in `jarvis_pipeline.py` — called at the top of every PowerSpec dispatch. Probes via `openclaw nodes list --json` + exec tool; if probe fails, auto-restarts the Scheduled Task via SSH (schtasks /end → kill node.exe → schtasks /run → wait 5s). No manual restart needed.
**Frequency:** Observed 2026-04-11 — first Option C smoke run hit this ~50 min after pairing.
**Added:** 2026-04-11

## 🟡 Windows path with space "Eric Brown" — quoting pitfalls (3rd occurrence)
**Pattern:** Paths containing "Eric Brown" in PowerShell commands, issued from a bash script over SSH, get split on the space because the outer `"..."` in bash conflicts with PowerShell's own `"..."` for path arguments. Error: `New-Item : A positional parameter cannot be found that accepts argument 'Brown\repos'.`
**Bad:**
```bash
ssh powerspec 'powershell -Command "Set-Location \"C:\Users\Eric Brown\repos\""'
```
**Good (single-quote inside PS):**
```bash
ssh powerspec "powershell -Command \"Set-Location 'C:\\Users\\Eric Brown\\repos'\""
```
**Rule of thumb:** In PowerShell, use single quotes `'...'` for paths. They're literal and don't conflict with the outer shell's double quotes.
**Also relevant for `scp`:** pass user via `-o User="Eric Brown"` (embedded quotes in the -o value), NOT `"Eric Brown@powerspec"` which scp's URL parser chokes on. See `powerspec-rebuild` CLI's SSH handling for the working pattern.
**Frequency:** 3 separate incidents this session. Add a unit test that asserts jarvis_pipeline.py's PowerShell command builders use single quotes.
**Added:** 2026-04-11

## 🟡 openclaw agent exec tool: stdout pipe hangs after remote process completes — FIXED 2026-04-11
**Pattern:** When `openclaw agent --agent main` issues an `exec` tool call with `host=<nodeId>` that pipes output through `cmd /c "... > _output.txt"`, the main agent's turn waits for the pipe to close even after the actual process (Claude Code on PowerSpec) has exited and written the output file. Orchestrator sees `stage_coder` as "running" for minutes past actual completion.
**Root cause (hypothesized):** `cmd /c` with stdout redirect (`>`) keeps the parent pipe file handle open until cmd.exe itself fully exits. If Claude Code's child process or a bg task inherited the handle, the pipe stays open.
**Fix applied:** Optimistic-timeout recovery pattern in `_dispatch_coder_powerspec()`: the outer `dispatch_agent` call is capped at 10 min (configurable). On timeout, the orchestrator checks `_output.txt` on PowerSpec via SSH. If content is present (>50 bytes), it treats the dispatch as successful and recovers the output via SSH read instead of waiting for the hung pipe. Logged as "pipe-hang recovery" in MC and jarvis-pipeline-mc.log.
**Added:** 2026-04-11

## 🟡 stage_quality cwd for remote-host tasks — FIXED 2026-04-11
**Pattern:** For tasks with `execution.coderHost = "powerspec"`, `task.repoPath` is a Windows path like `C:\Users\Eric Brown\repos\<task-id>`. `stage_quality` called `subprocess.run(cmd, cwd=repo, ...)` — which tried to use a Windows path as a cwd on macOS, raising `FileNotFoundError`.
**Fix applied:** `stage_quality` detects `coderHost == "powerspec"` and sets `cwd = str(Path.home())` instead. Unit test `test_e_stage_quality_uses_local_cwd_for_powerspec_tasks` asserts this.
**Rule:** For remote-host tasks, `verificationCmd` must SSH to the remote itself — the orchestrator's cwd just has to be a valid macOS dir.
**Added:** 2026-04-11

## 🟡 claude.cmd on Windows drops positional-prompt argv
**Pattern:** Running `claude.cmd --print "my prompt text"` as a subprocess on Windows (via openclaw exec tool or SSH) causes Claude Code to ignore the positional prompt entirely and return its idle greeting ("How can I help you?") or a vague "Could you clarify what you'd like me to reply to?" response.
**Root cause:** `claude.cmd` is a batch wrapper that uses `%*` to forward argv to `node cli.js`. The `%*` expansion on Windows has known issues with quoted arguments containing spaces, special characters, or when the enclosing process isn't a fully-quoted parent shell.
**Bad:**
```
["claude.cmd", "--print", "Respond with pong"]
```
Returns: `How can I help you?`
**Good (stdin pipe):**
```
["cmd", "/c", "echo Respond with pong | claude.cmd --print --dangerously-skip-permissions"]
```
Returns: `pong`
**Rule of thumb:** Always pipe the prompt into `claude.cmd` via stdin (`echo` or `type file.txt`). NEVER pass the prompt as a positional argument from non-interactive Windows subprocess contexts.
**Added:** 2026-04-11

## 🟡 PowerShell 5.x vs 7.x TLS Incompatibility
**Pattern:** PowerShell 5.x (default on Windows) fails TLS handshakes with modern endpoints. Remote Coder and Scheduled Tasks silently fail when using PS 5.x.
**Solution:** Always use PowerShell 7 (`pwsh`). Set Scheduled Tasks to use `pwsh.exe`, not `powershell.exe`. Verify with `$PSVersionTable.PSVersion`. PS 5.x → 7.x upgrade: `winget install Microsoft.PowerShell`.
**Frequency:** Remote Coder setup, Mar 4-5, 2026
**Added:** 2026-03-25
**Reference:** references/Remote_Session_Recap_EricBrown.docx
