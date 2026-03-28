## 🔬 System Smoke Test — 5:30 AM, Fri Mar 27 2026

**Health Score: 88/100** · 22/25 checks passed · 3 warnings · 0 failures

### ✅ All Clear
- Gateway: running (pid 61443), HTTP 200, OpenClaw 2026.3.24 up to date
- Tailscale: connected (100.101.203.113), Funnel active, all peers online
- Telegram bot: responding (1008ms)
- Google OAuth: valid, Gmail + Calendar APIs responding
- LLM providers: Anthropic, OpenAI, Grok, xAI all healthy
- API budget: $0.00 / $100.00 (0.0%)
- All 8 agents: configured with fallbacks
- Disk: 5% used (300 GiB free), uptime 11 days
- Security: no Dependabot alerts

### ⚠️ Warnings (Need Eric's Authorization)

1. **[MCP] Zapier MCP not responding** — May affect email send, Sheets, Dropbox integrations. Run: `mcporter list` to diagnose.

2. **[STABILITY] 44 LLM timeouts in recent logs** — Could indicate provider instability or overloaded API. Monitor; consider reducing concurrent agent calls if it continues.

3. **[AGENTS] Agent config files modified yesterday (2026-03-26)**
   - `main/AGENTS.md` (15:23)
   - `main/skills/google-oauth-reauth/SKILL.md` (15:19)
   - `main/skills/monitor/SKILL.md` (15:24)
   Please review if these changes were intentional.

4. **[SERVICE] com.openclaw.sessionmonitor LaunchAgent** — Exited with code 1. May need restart: `launchctl kickstart -k gui/$(id -u)/com.openclaw.sessionmonitor`

*Smoke test run: 2026-03-27 05:30:10 PDT*
