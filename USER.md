# USER.md - About Your Human

- **Name:** Eric Brown
- **What to call them:** Eric
- **Role:** CFO & COO of Cohesity
- **Timezone:** America/Los_Angeles (PST)
- **Cell:** 571 215 3060
- **Email:** ericfbrown1@gmail.com
- **Work Email:** Eric.brown@cohesity.com

## Family
- **Wife:** Hyun Ju Park (angie_hjpark@yahoo.com)

## Locations
- **Primary residence:** 162 James Avenue, Atherton CA 94027
- **Farm/vineyard:** 3553 Old Mission Road, Traverse City MI 49686 (tracked for IRS Form F)
  - **Farm vendors:** Agrivine (vineyard labor), Manigold Orchards (cherry/pear tree maintenance), Ginops (farm equipment)
- **Rental property 1:** 3469 Old Mission Road, Traverse City MI 49686 (managed by Soper Services)
- **Rental property 2:** 100 1st Street #209, Los Altos CA 94022
- **Lot (sold 2024):** 3503 Golf Club Drive, Lot #27, Clear Creek Tahoe, Carson City NV 89705
  - Purchased: Oct 16, 2020 for $795,500 (cash, no loan) + $50,000 social membership fee
  - Buyers: Eric Brown & Hyun-Ju Park (Brown Park Family Trust)
  - Closing: Signature Title Company LLC, Zephyr Cove NV

## Work
- **Company:** Cohesity
- **Office address:** 2625 Augustine Drive, Santa Clara CA
- **Commute:** 30 minutes from home (Atherton) to office (Tesla with FSD - can take short calls during commute)
- **Calendar:** Google Calendar integrated via gcalcli

## Interests & Hobbies
- **Boating:** Owns 2022 Princess F50 (kept in Sausalito CA)
- **Boat shopping:** Researching Marlow Explorer CB 58/62/66 and similar 58-66' boats
- **Future plans:** Cruising in Seattle, Puget Sound, SF Bay, Delta when retired
- **AI/Technology:** Learning OpenClaw use cases
- **Home office upgrades:** Interested in Apple Studio, Dell Alienware 16/18" laptops, and other high-end deals at MicroCenter Santa Clara

## Key Operating Rules

### ⚠️ CRITICAL: File Safety
**NEVER delete Eric's files under any circumstances.** This is the highest priority rule.
- Use `trash` if something absolutely must be removed (recoverable)
- When in doubt, ask first
- This applies to ALL files, not just obvious personal data

### 🚀 Code Deployment Default
- **All code projects default to Docker + Railway deployment** unless Eric says otherwise
- Always reference the `railway-deployment` skill when writing code
- Every project must include: Dockerfile, proper CMD with `${PORT:-8000}`, `.dockerignore`, and Railway-compatible env var handling
- No local file paths — all config via environment variables
- See `skills/railway-deployment/SKILL.md` for the full deployment standard

### Dropbox Storage
**NEW: Jarvis Dropbox Account (READ/WRITE)**
- Purpose: Store accumulated data from MacBook Pro to free up local storage
- Token: Configured in dropbox-cli.py (read/write access)
- Use: Move Project Scraper outputs and other large datasets on request
- Upload: `python3 ~/.openclaw/workspace/dropbox-cli.py upload <local> <dropbox_path>`
- List: `python3 ~/.openclaw/workspace/dropbox-cli.py list [path]`
- Download: `python3 ~/.openclaw/workspace/dropbox-cli.py download <path> [output]`

**Eric's Personal Dropbox (READ-ONLY)**
- Token: Old read-only token (still configured)
- Rule: NEVER delete, copy, edit, move, or modify any files in Eric's personal Dropbox

### Information Sharing & Privacy
- Never share Eric's information with anyone else unless he explicitly directs you to contact them.

### 1Password
**Jarvis 1Password Account (DEDICATED)**
- Purpose: Store credentials that Jarvis needs for automated tasks
- CLI: `op` v2.32.1 installed via Homebrew
- Account: Separate account for Jarvis only
- Authentication: via tmux sessions (required by 1Password CLI)
- **CRITICAL RULE: NEVER access Eric's personal 1Password account under any circumstances**

### API Tokens
- At the start of each run, reference the "Tokens" Google Doc to confirm the latest API credentials before using any services.

### LLM Usage & Cost Management
- **Default stack:** Favor lower-cost Claude 4.5 Sonnet or Grok 4 Fast for day-to-day work.
- **Research / deep analysis:** Use Claude 4.5 Opus or Grok 4.20 Beta when Eric explicitly asks for in-depth research or financial analysis, and flag any incremental cost before proceeding.
- **Cost awareness:** Do not exceed the current monthly plan limits; pause and confirm if spend could exceed them.
- **Payment alerts:** Always notify Eric if a task would require additional payment before proceeding.

### Email Rules
- **CC rule:** When sending emails from ericfbrown1@gmail.com, always cc: ericfbrown1@gmail.com
- **Work email:** Eric.brown@cohesity.com — include for financial analysis reports and work-related deliverables
- **Email footer:** Always append "Sent by Jarvis - AI assistant to Eric Brown" to emails

### Financial Analysis Workflow
- Assume the POV of an expert sell-side analyst: pull the latest earnings release, note the reporting period and fiscal calendar, and emphasize YoY ARR and GAAP revenue growth versus the prior four quarters.
- For guidance, take the midpoint of next quarter revenue/ARR, compute implied YoY growth, and compare it to the last five quarters of actuals; capture everything in a clear table.
- Evaluate cash flow, operating, and non-GAAP gross margin trends plus any product/use-case callouts driving performance; summarize valuation (revenue, ARR, non-GAAP operating income multiples).
- Use Claude Opus 4.6 or Grok 4.20 Beta for these deep dives, and deliver the final write-up as a Word document emailed to both ericfbrown1@gmail.com and Eric.brown@cohesity.com.

### Tax Preparation Workflow
- When asked to perform tax analysis or document collection/analysis for tax preparation, use all available Skills (Gmail search, Google Sheets, Dropbox, etc.) to gather and organize relevant documents and data.

### Daily Tasks
- **6 AM PT daily briefing email:** Include (1) Gmail tax/urgent items, (2) any same-day calendar conflicts, (3) **Top 5 Claude / Claude CoWork / Claude Code use cases for Cohesity** — scan trending posts, videos, blogs, and highly-rated secure GitHub projects each day for the best examples of Claude-powered automation that can improve Eric's efficiency at Cohesity across Salesforce, Snowflake, M365/OneDrive/SharePoint, Zoom, Workday, Slack; include links to sources and repos, (4) competitive/stock news for Rubrik, Commvault, and Veeam, (5) Anthropic ecosystem daily update—scan for new best practices, blog posts, changelog entries, and documentation updates for Claude Code, CoWork, Chat, Agent SDK, Skills, and MCP from anthropic.com, code.claude.com, support.claude.com, and the Anthropic blog—and (6) a quick system health/security update.
- **Sources for Claude use cases (section 3):** Search Twitter/X, YouTube, Reddit r/ClaudeAI, Hacker News, Product Hunt, GitHub trending, LinkedIn, and tech blogs for the latest Claude/CoWork/Code automation examples, workflows, and repos. Prioritize: (a) CFO/COO productivity wins, (b) enterprise SaaS integrations (Salesforce, Snowflake, Slack, M365), (c) financial analysis automation, (d) secure/tested GitHub repos with >50 stars, (e) novel CoWork scheduled tasks and plugin patterns.
- **Pre-briefing system checks:** Run `openclaw doctor`, install available OpenClaw updates, perform a security/port sweep for malware or misuse on the MacBook, and note any newly released standard OpenClaw skills.
- **Gmail monitoring:** Scan daily for tax-related or urgent messages; document qualifying tax items in the shared "Income Tax Tracking Items" Google Sheet with columns: date received, sender, description, type, Gmail link, comments/questions.
- **Competitive & market watch:** Keep an eye on stock/market updates for Rubrik, Commvault, and Veeam and flow notable changes into the next briefing.
- **Anthropic ecosystem watch:** Daily scan of anthropic.com/blog, code.claude.com/docs, support.claude.com, and Claude changelog for new features, best practices updates, security advisories, and Skills/MCP/CoWork improvements. Summarize any changes in the briefing.
- **MicroCenter price check:** Check MicroCenter Santa Clara for best prices on Apple Studio, Dell Alienware 16/18" laptops, and any other notable home office upgrade deals. Include standout deals in the daily briefing.

---

First contact: 2026-02-07
