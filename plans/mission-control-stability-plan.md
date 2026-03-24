# Mission Control Stability Plan (Mar 22, 2026)

## Root Cause Snapshot
1. **Frontend (Next.js) was running in dev mode (`next dev`) inside tmux with no supervisor.** When Turbopack crashed or the Mac slept, the process exited and stayed down.
2. **Backend ran only on localhost with no restart policy.** Manual tmux start kept it up since Thursday, but there was still no automatic recovery.
3. **No health checks / alerts.** Outages were only discovered when Eric hit the dashboard.
4. **macOS sleep on battery** repeatedly suspended the network stack, which kills Turbopack HMR sockets.
5. **Existing Docker Compose + restart policies in repo were never used.**

## Immediate Actions
- [x] Verified services via tmux (`mc-backend`, `mc-frontend`).
- [x] Restarted frontend with `-H 0.0.0.0` to restore remote access.
- [x] Tested reachability from PowerSpec PC (`curl http://100.101.203.113:3000`).

## Remediation Roadmap

### Step 1 — Process Manager
- Install `pm2`, create `ecosystem.config.js` for backend + frontend (use `next start`, not `next dev`).
- Run `pm2 save && pm2 startup` so launchd restarts services on boot.

### Step 2 — Production Build
- Switch to `npm run build && npm run start` for Next.js; Turbopack dev server is not production-safe.

### Step 3 — Containerize & Deploy
- Use the existing `Dockerfile`/`docker-compose.yml` (add backend service) with `restart: unless-stopped`.
- Deploy the containers to Railway for hands-off hosting.

### Step 4 — Health Checks + Alerts
- Add `/health` endpoint in Express; use Railway health checks and/or cron-based HTTP checks that alert via Telegram.

### Step 5 — Monitoring + Logs
- Integrate `prom-client` + Winston; aggregate logs via Railway or Datadog.

### Step 6 — Regression Tests
- Jest + Cypress suites run via GitHub Actions before deploys.

### Step 7 — Power Management
- Use `caffeinate` or keep Mac plugged in; ensure `pmset -c sleep 0` is enforced during server duty.

## References
- Internal RCA (`dashboard-rca-opus`, Grok 4.2 stability plan)
- macOS pmset logs (Mar 18 battery sleep)
- Curl tests from PowerSpec PC verifying uptime
