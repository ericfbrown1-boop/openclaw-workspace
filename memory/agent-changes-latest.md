### 🤖 Your 8 Agents — What They Do

**🤖 Jarvis** (main) — Primary orchestrator & personal assistant
  Handles all direct requests, delegates to specialized agents, manages daily briefings, email, calendar, web research, file management, and conversation

**🔍 Researcher** (researcher) — Deep research & financial analysis
  Financial earnings analysis (Rubrik, Commvault, Veeam), competitive intelligence, market research, fact-checking, delivers Word doc reports

**📐 Planner** (planner) — Architecture & project planning
  Designs new projects, creates PLAN.md files, defines tech stacks, writes architecture docs. Drafts with Opus 4.6, stress-tested by Grok 4.20 Beta adversarial review

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
- **Build a Project** — "Build [description]" — Full pipeline: Researcher → Planner (Opus) → Grok 4.20 Beta adversarial review → Coder → Quality (Grok 4.20 Beta) → Auditor → Conductor deploys to Railway
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
