# OpenClaw Daily Smoke Test
**Run:** 2026-04-10 05:30:07 PDT
**Host:** Mac

## 1. Gateway Health

  Installed: OpenClaw 2026.4.9 (0512059)
  Latest available: 2026.4.9
  ✅ OpenClaw is up to date
  ✅ Gateway process running (pid 13358)
  ✅ Gateway HTTP health check passed (HTTP 200)

## 2. Tailscale Connectivity ⚡

  State: Running
  Self: erics-macbook-pro (100.101.203.113)
  Online: True
  Peers:
    powerspecpc: 100.81.21.114 (🟢 online)
    localhost: 100.86.157.19 (🟢 online)
  ✅ Tailscale running and connected (100.101.203.113)
  ✅ Tailscale CLI: /usr/local/bin/tailscale (correct)
  ⚠️  Tailscale Funnel not detected for voice calls

## 3. Telegram Bot Health ⚡

  ✅ Telegram bot responding (317ms)
  ⚠️  Telegram streaming: {'mode': 'partial'} (consider 'partial' for better UX)
  ✅ Telegram retry attempts: 10

## 4. Google OAuth Token

  ✅ Google OAuth token present (issued: 2026-04-10T03:59:15Z)
  ✅ Gmail API responding
  ✅ Calendar API responding

## 5. Zapier MCP Integration

  ⚠️  Zapier MCP may not be responding

## 6. LLM Provider Health

  ✅ anthropic:default (anthropic): healthy, last used never
  ✅ openai:default (openai): healthy, last used never
  ✅ grokheavy:default (grokheavy): healthy, last used never
  ✅ xai:default (xai): healthy, last used never
  ✅ LLM timeout: 180s (good — fast failover)
  ⚠️  49 LLM timeouts in recent logs

## 6.5 API Usage & Budget

  Monthly spend: $0.00 / $100.00 (0.0%)
  Today's spend: $0.0000
  Projected monthly: $0.00
  Days remaining: 21
  Daily tokens: 0 in / 0 out
  Monthly tokens: 0 in / 0 out
  Alert level: none
  ✅ Budget healthy (0.0% used)
  ✅ API budget within limits (0.0%)

## 7. Agent Configuration

  Agents: 8
  ✅ main: anthropic/claude-opus-4-6 +2 fallbacks workspace=✅
  ✅ researcher: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ planner: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ coder: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ quality: anthropic/claude-sonnet-4-6 +1 fallbacks workspace=✅
  ✅ monitor: anthropic/claude-sonnet-4-6 +1 fallbacks workspace=✅
  ✅ auditor: anthropic/claude-sonnet-4-6 +1 fallbacks workspace=✅
  ✅ conductor: anthropic/claude-sonnet-4-6 +1 fallbacks workspace=✅

## 8. LaunchAgent Services

  ✅ com.openclaw.tailscale.monitor (exit=0, pid=-)
  ✅ com.openclaw.batteryguard (exit=0, pid=-)
  ✅ com.openclaw.heartbeat (exit=0, pid=-)
  ✅ ai.openclaw.gateway (exit=0, pid=13358)
  ✅ com.openclaw.weeklysecurity (exit=0, pid=-)
  ✅ com.openclaw.logrotation (exit=0, pid=-)
  ✅ com.openclaw.gatewaywatchdog (exit=0, pid=-)
  ✅ com.openclaw.caffeinate (exit=0, pid=21190)
  ✅ com.openclaw.selfheal (exit=0, pid=-)
  ⚠️  com.openclaw.sessionmonitor (exit=1)

## 9. System Resources

  ✅ Disk: 4% used (299Gi free)
  ✅ Log directory: 10M
  ✅ Session store: 42M
  System: up 25 days

## 10. Security

  ⚠️  Dependabot: 3 high alerts

## 11. Software Updates

  ✅ Node.js: v25.6.1
  ✅ npm: 11.9.0
  ✅ mcporter: 0.7.3
  ✅ gog CLI: v0.9.0 (99d9575 2026-01-22T04:15:12Z)

## 12. Agent Skills & Configuration Changes

### 🤖 Your 8 Agents — What They Do

**🤖 Jarvis** (main) — Primary orchestrator & personal assistant
  Handles all direct requests, delegates to specialized agents, manages daily briefings, email, calendar, web research, file management, and conversation

**🔍 Researcher** (researcher) — Deep research & financial analysis
  Financial earnings analysis (Rubrik, Commvault, Veeam), competitive intelligence, market research, fact-checking, delivers Word doc reports

**📐 Planner** (planner) — Architecture & project planning
  Designs new projects, creates PLAN.md files, defines tech stacks, writes architecture docs. Uses GPT 5.4 + cross-review loop

**💻 Coder** (coder) — Code implementation
  Writes code from PLAN.md specs, builds scripts, generates reports, creates Dockerfiles. Reads PLAN.md before writing any code

**🛡️ Quality** (quality) — Security audit & error diagnosis
  Part A: Diagnoses errors/crashes. Part B: Security audits (secret scanning, git history, .gitignore, dependencies, Tailscale config). Prepares BFG commands for Jarvis

**📊 Monitor** (monitor) — Stock watch & price monitoring
  Tracks Rubrik/Commvault/Veeam stock prices, MicroCenter Santa Clara deals (Apple Studio, Alienware), system health alerts

**📋 External Auditor** (auditor) — Final code review & packaging
  Verifies code is clean post-Quality audit, asks Eric about Grok review, packages code with repomix for external review

**🚂 Conductor** (conductor) — DevOps & Railway deployment
  Docker builds, Railway deployments, smoke tests, Celery worker setup, MinIO deployment, infrastructure verification. Follows Railway Deployment Skill (13 sections)

---

### 🎯 Invokable Skills & Capabilities
*Say any of these to Eric's Jarvis:*

**📊 Financial & Business**
- **Financial Earnings Analysis** — "Run financial analysis on [company] quarterly results" — Full sell-side analyst report with ARR, revenue, margins, valuation. Delivered as Word doc + email
- **Competitive Intelligence** — "Research [company]" — Deep competitive analysis using web research + Project Scraper data
- **Contract Analysis** — "Run Contract Analyzer on [files]" — AI-powered legal contract review with 17-section report, risk flags, entity attribution (Cohesity/Arctera)

**💻 Code & Deployment**
- **Build a Project** — "Build [description]" — Full pipeline: Planner → GPT review → Coder → Tester → Quality audit → Conductor deploys to Railway
- **Railway Deployment** — "Deploy [project] to Railway" — Docker build, Railway config, Celery workers, MinIO, smoke tests
- **Security Audit** — "Run security audit on [repo]" — Secret scanning, git history check, dependency vulnerabilities, BFG cleanup
- **Code Review** — "Review [repo/PR]" — Quality + External Auditor pipeline, optional Grok cross-review via repomix

**📧 Communication & Productivity**
- **Send Email** — "Email [person] about [topic]" — Via gog CLI or Zapier MCP, with attachments, CC rules applied
- **Search Email** — "Find emails about [topic]" — Gmail search via gog or Zapier MCP
- **Calendar Check** — "What's on my calendar?" — Google Calendar via gog CLI
- **Google Sheets** — "Update/read [spreadsheet]" — Read/write rows via Zapier MCP or gog CLI
- **Dropbox Search** — "Find [file] in Dropbox" — Search Eric's personal Dropbox via Zapier MCP

**🔍 Research & Information**
- **Web Research** — "Research [topic]" — Web search + fetch, synthesized summary
- **YouTube/Podcast Summary** — "Summarize [URL]" — Transcript extraction + AI summary
- **Weather** — "What's the weather in [location]?" — Current conditions + forecast
- **Place Search** — "Find [type of place] near [location]" — Google Places API

**🔧 System & Automation**
- **System Status** — "Status" — Full MacBook health: gateway, disk, Tailscale, Gmail, self-heal, errors
- **Health Check** — "Run healthcheck" — Deep security scan of the MacBook
- **Voice Call** — "Call me" — Twilio voice call via Tailscale Funnel
- **Cron Jobs** — "Schedule [task] at [time]" — Create/manage recurring automation
- **GitHub Operations** — "Check PR/issues on [repo]" — PR status, CI, code review, API queries

**🎯 Daily Automated Tasks**
- **6 AM Daily Briefing** — Automatic — Gmail, calendar, AI ideas, competitive news, MicroCenter deals, system health
- **5:30 AM Smoke Test** — Automatic — 24-check system diagnostic with action items
- **5 AM Doctor --fix** — Automatic — Auto-repair config issues
- **Tax Email Scan** — Automatic — Weekly Gmail scan for tax items → Google Sheet
- **Stock Monitor** — Automatic — Rubrik, Commvault, Veeam price tracking
- **Alex Finn YouTube Watch** — Automatic — Daily monitoring for OpenClaw enhancement ideas

---

### 📝 Agent Configuration Changes

**🆕 Newly tracked:**
- `monitor/skills/afrexai-contract-analyzer/SKILL.md`
- `monitor/skills/ai-legal-assistant/SKILL.md`
- `monitor/skills/auditor/SKILL.md`
- `monitor/skills/autoClaw/SKILL.md`
- `monitor/skills/blogwatcher/SKILL.md`
- `monitor/skills/blucli/SKILL.md`
- `monitor/skills/cohesity-domain/SKILL.md`
- `monitor/skills/competitive-intel/SKILL.md`
- `monitor/skills/earnings-analyzer/SKILL.md`
- `monitor/skills/financial-report-gen/SKILL.md`
- `monitor/skills/firecrawl/SKILL.md`
- `monitor/skills/gog/SKILL.md`
- `monitor/skills/google-oauth-reauth/SKILL.md`
- `monitor/skills/librarian/SKILL.md`
- `monitor/skills/linkedin-carousel/SKILL.md`
- `monitor/skills/monitor/SKILL.md`
- `monitor/skills/peekaboo/SKILL.md`
- `monitor/skills/project-dynamo/SKILL.md`
- `monitor/skills/ragflow-search/SKILL.md`
- `monitor/skills/railway-deployment/SKILL.md`
- `monitor/skills/remote-coder/SKILL.md`
- `monitor/skills/salesforce-analytics/SKILL.md`
- `monitor/skills/slack-teams-hub/SKILL.md`
- `monitor/skills/snowflake-sql/SKILL.md`
- `monitor/skills/tailscale-troubleshooting/SKILL.md`
- `monitor/skills/tax-automation/SKILL.md`
- `monitor/skills/workday-analytics/SKILL.md`

  ✅ No unexpected agent configuration changes

## Summary

**Health Score: 80/100** (20/25 checks passed, 5 warnings, 0 failures)

## 🔔 Action Items for Eric

1. [TAILSCALE] Voice calls may not work — run: tailscale serve --bg 3334 && tailscale funnel --bg 3334
2. [TELEGRAM] Enable streaming: set channels.telegram.streaming = 'partial' in config
3. [MCP] Check Zapier MCP connection — run: mcporter list
4. [STABILITY] Frequent LLM timeouts detected (49) — may indicate provider issues or overloaded API
5. [SECURITY] 3 high-severity Dependabot alerts — review and patch

---
*Generated by OpenClaw Daily Smoke Test v1.0 at 2026-04-10 05:30:16 PDT*
