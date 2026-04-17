# RCA: OpenClaw Web Client Stall — 2026-04-13

## Symptoms
- Web UI at `127.0.0.1:18789` appeared stalled/frozen around 21:00–21:15 PDT
- `sessions.list` polled every ~2 seconds by browser client (conn=702a9844), returning 177 sessions
- Sessions JSON file: **5.2 MB** (107 session entries with full history)

## Root Causes Found

### 1. PRIMARY — Session File Lock Contention
**Evidence:** Gateway log at `20:30:29` shows:
```
Error: session file locked (timeout 10000ms): unknown ~/.openclaw/agents/main/sessions/sessions.json.lock
```
The 5.2 MB `sessions.json` file is locked during read/write operations. When multiple concurrent operations (agent runs, subagent spawns, web UI polling) all compete for the lock, the 10-second timeout is hit and the request fails with `UNAVAILABLE`. The web UI's 2-second polling interval means it immediately retries, creating further contention.

### 2. CONTRIBUTING — Missing `subagent-registry.runtime.js` Module
**Evidence:** Repeated errors in gateway log:
```
[warn] subagent cleanup finalize failed (e942b871…): Error [ERR_MODULE_NOT_FOUND]: Cannot find module 'subagent-registry.runtime.js'
```
The file `subagent-registry-CflSFWBm.js` references `./subagent-registry.runtime.js` which does not exist in the dist folder. This causes subagent cleanup to fail repeatedly for session `e942b871`, potentially holding locks longer than necessary and contributing to lock contention. This appears to be a **bug in OpenClaw 2026.4.12**.

### 3. CONTRIBUTING — Gateway Restart Race Condition (~20:18 PDT)
**Evidence:** Gateway log shows:
```
20:18:51 chat.history unavailable during gateway startup
20:18:51 models.list unavailable during gateway startup
20:18:52-54 repeated chat.history UNAVAILABLE
```
A gateway restart occurred around 20:18. During startup, the web client received UNAVAILABLE errors, and the 2s polling amplified the load during the recovery window. The session lock timeout at 20:30 followed 12 minutes after, suggesting recovery-period contention.

### 4. CONTRIBUTING — High Session Count & Large Payload
**Evidence:** 177 sessions, 5.2 MB sessions.json, ~55ms per `sessions.list` call.
Each poll serializes the entire 5.2 MB file to JSON and sends it over WebSocket. At 2-second intervals, this is ~2.6 MB/s of JSON serialization overhead continuously.

## Timeline
| Time (PDT) | Event |
|---|---|
| 20:18 | Gateway restart; web clients get UNAVAILABLE errors |
| 20:18-20:30 | Recovery period; subagent cleanup failures (missing module) |
| 20:30:10 | Another subagent cleanup failure |
| 20:30:29 | **Session file lock timeout (10s)** — agent request fails |
| 20:31:57 | Another subagent cleanup failure |
| ~21:00-21:15 | Eric observes UI stall |
| 21:16 | Webchat disconnects (code=1001) |
| 21:17+ | Sessions.list calls succeeding normally (~55ms) |

## Fixes Applied
1. **Task maintenance** — Ran `openclaw tasks maintenance --apply`: pruned 1 stale task-flow. 15 audit errors and 565 audit warnings remain (non-blocking, informational).
2. **Verified lock file cleared** — No stale `.lock` file present at time of investigation.
3. **Confirmed MC hardcoded IP fix** — No references to old IP `188.141.203.113` in JarvisMissionControl `.next/` build. Fix from prior session is confirmed applied.
4. **Confirmed MC frontend running** — PM2 shows `mission-control-frontend` online (pid 28884, 2 restarts, 45m uptime), backend online (pid 1010, 11h uptime). HTTP 200 on localhost:3000.
5. **Confirmed gateway healthy** — `openclaw status` shows running, 38ms latency, pid 28129, up to date.

## Fixes Remaining (requires OpenClaw update or Eric approval)

### A. Missing `subagent-registry.runtime.js` (OpenClaw Bug)
The file `subagent-registry.runtime.js` is referenced but doesn't exist in the dist. This is an OpenClaw packaging bug in 2026.4.12. The failed cleanup for session `e942b871` will keep retrying and logging warnings until either:
- OpenClaw releases a fix
- The zombie session `e942b871` is manually removed

### B. Session Bloat — Consider Periodic Cleanup
177 sessions / 5.2 MB is heavy. Old completed sessions could be archived or pruned to reduce:
- Lock contention window (smaller file = faster I/O)
- Polling payload size
- Memory usage

### C. Web Client Polling Interval
The 2-second polling interval for `sessions.list` is aggressive for 177 sessions. This is an OpenClaw web client design decision — no user-side fix available. A future OpenClaw update could:
- Use WebSocket push instead of polling
- Increase interval based on session count
- Return only changed sessions (delta)

## Prevention
1. **Monitor session count** — Alert if sessions exceed 150; consider periodic cleanup.
2. **Watch for OpenClaw updates** — The `subagent-registry.runtime.js` bug may be fixed in a future release.
3. **Gateway restart awareness** — After any gateway restart, expect 1-2 minutes of elevated lock contention as clients reconnect and poll simultaneously.
4. **Session file size monitoring** — If `sessions.json` exceeds 10 MB, proactively clean up old sessions.
