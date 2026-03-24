# OpenClaw Daily Smoke Test
**Run:** 2026-03-22 05:30:11 PDT
**Host:** Mac

## 1. Gateway Health

  Installed: OpenClaw 2026.3.13 (61d171a)
  Latest available: 2026.3.13
  ✅ OpenClaw is up to date
  ✅ Gateway process running (pid 40865)
  ✅ Gateway HTTP health check passed (HTTP 200)

## 2. Tailscale Connectivity ⚡

  State: Running
  Self: Eric’s MacBook Pro (100.101.203.113)
  Online: True
  Peers:
    funnel-ingress-node: fd7a:115c:a1e0::9d01:a6ac (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:626f:140a (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::5201:b0a3 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::401:c29f (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::1e01:7098 (🟢 online)
    localhost: 100.86.157.19 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::b601:dd8b (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::3f01:58a5 (🟢 online)
    remote-coder-main: 100.67.128.123 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::5c01:d68c (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:6259:5f05 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0:ab12:4843:cd96:625f:d761 (🟢 online)
    funnel-ingress-node: fd7a:115c:a1e0::ac01:85a5 (🟢 online)
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

  ✅ Telegram bot responding (968ms)
  ✅ Telegram streaming: partial (reduces perceived latency)
  ✅ Telegram retry attempts: 5

## 4. Google OAuth Token

  ✅ Google OAuth token present (issued: 2026-03-17T10:56:55Z)
  ✅ Gmail API responding
  ✅ Calendar API responding

## 5. Zapier MCP Integration

  ✅ Zapier MCP server healthy (20 tools)

## 6. LLM Provider Health

  ✅ anthropic:default (anthropic): healthy, last used 67.3h ago
  ✅ openai:default (openai): healthy, last used 0.5h ago
  ✅ grokheavy:default (grokheavy): healthy, last used never
  ✅ xai:default (xai): healthy, last used 117.0h ago
  ✅ LLM timeout: 180s (good — fast failover)
  ✅ Minor LLM timeouts: 4 (within normal range)

## 7. Agent Configuration

  Agents: 8
  ✅ main: openai/gpt-5.1-codex +3 fallbacks workspace=✅
  ✅ researcher: xai/grok-4.20 +3 fallbacks workspace=✅
  ✅ planner: openai/gpt-5.4 +3 fallbacks workspace=✅
  ✅ coder: anthropic/claude-opus-4-6 +3 fallbacks workspace=✅
  ✅ quality: anthropic/claude-opus-4-6 +1 fallbacks workspace=✅
  ✅ monitor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ auditor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅
  ✅ conductor: anthropic/claude-sonnet-4-6 +2 fallbacks workspace=✅

## 8. LaunchAgent Services

  ✅ com.openclaw.tailscale.monitor (exit=0, pid=-)
  ✅ ai.openclaw.gateway (exit=0, pid=40865)
  ✅ com.openclaw.weeklysecurity (exit=0, pid=-)
  ✅ com.openclaw.logrotation (exit=0, pid=-)
  ✅ com.openclaw.gatewaywatchdog (exit=0, pid=-)
  ✅ com.openclaw.selfheal (exit=0, pid=-)
  ⚠️  com.openclaw.sessionmonitor (exit=1)

## 9. System Resources

  ✅ Disk: 5% used (306Gi free)
  ✅ Log directory: 2.7M
  ✅ Session store: 18M
  System: up 6 days

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

No changes detected since last check. ✅
  ✅ No unexpected agent configuration changes

## Summary

**Health Score: 95/100** (23/24 checks passed, 1 warnings, 0 failures)

## 🔔 Action Items for Eric

1. [SECURITY] 3 high-severity Dependabot alerts — review and patch

---
*Generated by OpenClaw Daily Smoke Test v1.0 at 2026-03-22 05:30:20 PDT*
