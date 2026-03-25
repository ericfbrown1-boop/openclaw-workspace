# OpenClaw Daily Smoke Test
**Run:** 2026-03-25 12:52:07 PDT
**Host:** Erics-MacBook-Pro.local

## 1. Gateway Health

  Installed: OpenClaw 2026.3.23-2 (7ffe7e4)
  Latest available: 2026.3.24
  ⚠️  Update available: 2026.3.23 → 2026.3.24
  ✅ Gateway process running (pid 52211)
  ✅ Gateway HTTP health check passed (HTTP 200)

## 2. Tailscale Connectivity ⚡

  State: Running
  Self: Eric’s MacBook Pro (100.101.203.113)
  Online: True
  Peers:
    funnel-ingress-node: fd7a:115c:a1e0::af01:ada1 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::9d01:a6ac (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:626f:140a (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::5201:b0a3 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::401:c29f (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::f701:f79c (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::1e01:7098 (🟢 online)
    localhost: 100.86.157.19 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::b601:dd8b (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::3f01:58a5 (🟢 online)
    remote-coder-main: 100.67.128.123 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::5c01:d68c (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:6259:5f05 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:625f:d761 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::ac01:85a5 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::c001:f7a7 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:625a:9516 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::c301:f2b1 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:6268:d02b (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::5a01:aea3 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:6249:ba61 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::4b01:bda1 (🟢 online)
  ✅ Tailscale running and connected (100.101.203.113)
  ✅ Tailscale CLI: /usr/local/bin/tailscale (correct)
  ✅ Tailscale Funnel active (voice call webhook)

## 3. Telegram Bot Health ⚡

  ✅ Telegram bot responding (1018ms)
  ✅ Telegram streaming: partial (reduces perceived latency)
  ✅ Telegram retry attempts: 5

## 4. Google OAuth Token

  ✅ Google OAuth token present (issued: 2026-03-25T17:32:43Z)
  ✅ Gmail API responding
  ✅ Calendar API responding

## 5. Zapier MCP Integration

  ✅ Zapier MCP server healthy (20 tools)

## 6. LLM Provider Health

  ✅ anthropic:default (anthropic): healthy, last used 6.7h ago
  ✅ openai:default (openai): healthy, last used 26.0h ago
  ✅ grokheavy:default (grokheavy): healthy, last used never
  ✅ xai:default (xai): healthy, last used 1.8h ago
  ✅ LLM timeout: 180s (good — fast failover)
  ⚠️  42 LLM timeouts in recent logs

## 6.5 API Usage & Budget

  Monthly spend: $0.00 / $100.00 (0.0%)
  Today's spend: $0.0000
  Projected monthly: $0.00
  Days remaining: 7
  Daily tokens: 0 in / 0 out
  Monthly tokens: 0 in / 0 out
  Alert level: none
  ✅ Budget healthy (0.0% used)
  ✅ API budget within limits (0.0%)

## 7. Agent Configuration

  Agents: 8
  ✅ main: anthropic/claude-opus-4-6 +3 fallbacks workspace=✅
  ✅ researcher: xai/grok-4.20 +3 fallbacks workspace=✅
  ✅ planner: openai/gpt-5.4 +3 fallbacks workspace=✅
  ✅ coder: anthropic/claude-opus-4-6 +3 fallbacks workspace=✅
  ✅ quality: anthropic/claude-opus-4-6 +1 fallbacks workspace=✅
  ✅ monitor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ auditor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ conductor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅

## 8. LaunchAgent Services

  ✅ com.openclaw.tailscale.monitor (exit=0, pid=-)
  ✅ ai.openclaw.gateway (exit=0, pid=52211)
  ✅ com.openclaw.weeklysecurity (exit=0, pid=-)
  ✅ com.openclaw.logrotation (exit=0, pid=-)
  ✅ com.openclaw.gatewaywatchdog (exit=0, pid=-)
  ✅ com.openclaw.caffeinate (exit=0, pid=21190)
  ✅ com.openclaw.selfheal (exit=0, pid=-)
  ⚠️  com.openclaw.sessionmonitor (exit=1)

## 9. System Resources

  ✅ Disk: 5% used (302Gi free)
  ✅ Log directory: 4.1M
  ✅ Session store: 28M
  System: up 9 days

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

**📝 Modified:**
- `main/AGENTS.md` — updated 2026-03-25 12:45 (115 lines)
- `main/skills/monitor/SKILL.md` — updated 2026-03-25 12:45 (215 lines)

**🆕 Newly tracked:**
- `main/skills/auditor/SKILL.md`

  ⚠️  Agent configuration files have been modified since last check

## Summary

**Health Score: 84/100** (21/25 checks passed, 4 warnings, 0 failures)

## 🔔 Action Items for Eric

1. [UPDATE] Run: npm install -g openclaw@latest (current: 2026.3.23, available: 2026.3.24)
2. [STABILITY] Frequent LLM timeouts detected (42) — may indicate provider issues or overloaded API
3. [SECURITY] 3 high-severity Dependabot alerts — review and patch
4. [AGENTS] Review agent configuration changes in the Agent Skills section above

---
*Generated by OpenClaw Daily Smoke Test v1.0 at 2026-03-25 12:52:16 PDT*
