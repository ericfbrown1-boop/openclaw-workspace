# MEMORY.md — Jarvis Long-Term Memory

## Project Scraper
- Built together with Eric in a prior Claude Code session (before reboot ~Feb 2026)
- Lives at: `~/ProjectScraper/`
- Node.js + Playwright web crawler for competitive intelligence
- Crawls company websites: maps site structure, extracts content, samples docs, outputs to Google Sheets
- Code: `~/ProjectScraper/code/` (crawler.js, crawler_v2.js, extract_sitemap.js, process_urls.js)
- Completed research on: Rubrik, Commvault, Veeam, Cohesity, BI Tools, Sentra, EverQuote, AI Cluster
- Also produced "Build_Your_Own_Jarvis_Complete_Guide.docx"

## Context
- Eric is CFO & COO of Cohesity — competitive intel on data protection/backup vendors is highly relevant
- First target was Rubrik.com (direct competitor)
- Project went through 6+ phases of development with Claude Code

## Voice Calls
- Voice calls fully working as of 2026-02-23
- Provider: Twilio, from number +18333027822
- Voice: Twilio default (ElevenLabs streaming attempted but not working yet)
- Mode: notify (reliable, one-way announcements)
- Webhook exposed via Tailscale Funnel: https://erics-macbook-pro.tail1e87b8.ts.net/voice/webhook
- Tailscale must be running for calls to work (App Store app, login: ericfbrown1@gmail.com)
- publicUrl set in openclaw.json voice-call config
- If calls break: check `tailscale serve status` and `tailscale funnel status`
- To re-expose: run `tailscale serve --bg 3334 && tailscale funnel --bg 3334`
- DO NOT delete ~/.openclaw/extensions/voice-call — it enables publicUrl support in config schema
- staleCallReaperSeconds and tunnel config fields are NOT supported (schema rejects them)

## Google OAuth / gog CLI
- gog CLI v0.9.0 configured with ericfbrown1@gmail.com
- Services: gmail, calendar, contacts, drive, docs, sheets
- Google Sheets API and Drive API both enabled (project 672907822296)
- Token stored in macOS Keychain (service: "gogcli", account: "token:default:ericfbrown1@gmail.com")
- Re-authed Mar 9, 2026 using `gog auth add ... --force-consent` after deleting stale keychain entry
- **Known bug:** `gog gmail send` with `--body-file` or `--attach` hangs indefinitely; simple `--body "text"` works. Needs investigation.

## Hong Kong Trip
- March 11-13, 2026, Hong Kong Island
- Wants harbor view room
- Top picks: Four Seasons (Central/IFC), Mandarin Oriental, Conrad, Island Shangri-La, Upper House

## CGT (Chateau Grand Traverse) — Pricing Issue
- Email from Eddie (Feb 2026): claims $8,496.15 overpayment 2024-2025 due to Pinot Gris Brix base error (19° vs contracted 22°)
- CGT proposes credit $8,496.15 to 2026 + price increase ($1,725→$1,750/ton, PG Brix base 22°→21°)
- CONTRACT IN DROPBOX — need to verify 22.0° Brix is indeed the contracted PG base

## Dropbox
- Jarvis Dropbox account (READ/WRITE) — token auto-refreshes via dropbox-cli.py
- **`/Jarvis Reports/`** — standard folder for all generated reports (created Mar 9, 2026)
- **`/Jarvis Backups/`** — config and workspace backups
- Dropbox app lacks `sharing.write` scope — can't generate shareable links via API
- Eric's personal Dropbox token EXPIRED Feb 26, 2026 — Eric needs to refresh at dropbox.com/developers

## Backup & Restore
- Full backup procedure documented: 13 steps, bare Mac → fully running Jarvis
- Latest backup: `/Jarvis Backups/2026-03-09/jarvis_full_backup_20260309.tar.gz` (20MB)
- Restore procedure: `/Jarvis Reports/Jarvis_Full_Restore_Procedure.md`
- Only manual steps: API keys (Tokens doc), Google OAuth (browser sign-in), cron recreation
- Eric confirmed: "Can I fully restore you from backup?" → Yes

## Daily Briefing (6 AM PT cron)
- Sections: Gmail urgent/tax, Calendar, AI automation ideas, Competitive/stock news, MicroCenter deals, OpenClaw System Health & Security
- Health section includes: version check, security audit, vulnerabilities/patches, gateway uptime, self-heal status, doctor output, Dependabot alerts
- Fallback: if email fails, save to Dropbox `/Jarvis Reports/` and notify via Telegram
- Cron ID: c79c8317-5cf7-4e01-b170-a849094a6265

## Self-Heal Infrastructure
- Gateway watchdog, self-heal script, log rotation, Tailscale monitor, session monitor — all LaunchAgents
- Doctor --fix runs at 5 AM PT daily
- Self-heal checks every 10 minutes

## Identity
- Name: Jarvis
- First established: 2026-02-07
- Memory wiped at some point, reconnected ~2026-02-23

## GPT 5.4 Trial (HISTORICAL — 2026-03-11 to 2026-03-27, replaced by Grok 4.20 Beta)
- Eric approved trial of GPT 5.4 (openai/gpt-5.1-codex) for subagent work (2026-03-11 to 2026-03-27)
- Primary use was: Cross-review loop for Planner output (dual-model architecture review)
- Inspired by Alex Finn's recommendation (switched from Opus to 5.4 for speed)
- Jarvis main model stayed Opus 4.6 — GPT 5.4 was a reviewer/second opinion
- Trial ended 2026-03-27 with the "Dual-Model Planning Process" standing change: adversarial review moved from GPT 5.4 to Grok 4.20 Beta (`xai/grok-4.20`). See DELEGATION.md Stage 3.
- 2026-04-11: Quality Agent also moved to Grok 4.20 Beta for the same reason (adversarial output-correctness judgment is its core skill).

## Alex Finn YouTube Monitoring (Started 2026-03-11)
- Eric requested daily monitoring of Alex Finn's YouTube for OpenClaw enhancement ideas
- Digest saved at: memory/alexfinn-digest.md
- Use `summarize` CLI to pull YouTube transcripts
- Key videos reviewed: "100 hours of lessons", "Mission Control", "INCREDIBLE" (Mar 11 livestream)
- Include "Finn Digest" in daily briefings with 2-3 actionable suggestions

## Security Rule Updates (2026-03-11)
- NEVER access Moltbook, Discord forums, or any OpenClaw community forums (security risk)
- Added to TOOLS.md + all agent AGENTS.md files (Researcher, Planner, Coder)
- Build your own skills by reading others' code, don't install third-party skills

## Docker-First / Railway Deployment Standard (2026-03-11)
- All code projects must be Docker-first, Railway-ready from line one
- Updated Researcher, Planner, and Coder AGENTS.md files
- Every project: Dockerfile + docker-compose.yml + .env.example + railway.json + CI workflow
- No local file paths, all config via env vars, bind to $PORT, stateless processes

## FinancialReportApp — Production-Grade (2026-03-28)
- Full pipeline working: crawl IR site → Claude structured outputs → .docx → email
- Lives at: `~/FinancialReportApp/` | GitHub: `ericfbrown1-boop/FinancialReportApp`
- Deployed on PowerSpec Docker: frontend :3001, API :8001, Postgres :5433, Redis :6380
- Frontend login: admin / Ajax
- **Structured outputs**: Anthropic `output_config/json_schema` — no more manual JSON parsing
  - Anthropic limitations: no min/max on numbers, no minItems>1 on arrays
- **Quality gates**: 3 gates in generate_report_docx(), all BLOCKING (raise ValueError)
  - Gate 1: >3 of 6 required fields missing → reject
  - Gate 2: all 6 fields missing → reject immediately
  - Gate 3: .docx verification — >7 "not available" or <1500 chars → delete and reject
- **Retry**: exponential backoff on 429/5xx/timeout (3 attempts, 2^n delay)
- **Crawler**: 3-strategy IR discovery — HTML link extraction (best for ASP.NET sites), Firecrawl map, pattern probing
- **Output parity**: SHA256 hash verified — download === email attachment
- **Test suite**: 33 tests in api/tests/ (pytest)
- **Env validation**: validate_environment() checks API key prefix+length, DB, Redis, Firecrawl on startup
- **Timing metrics**: TIMING prefix in logs for crawl/tag/synthesize/generate phases

## Dual-Model Planning Process (2026-03-28)
- All plans: Research → Opus 4.6 draft → Grok 4.20 Beta adversarial review
- Replaces GPT-5.4 cross-review
- DELEGATION.md + PIPELINE.md updated

## Standing Rules Added (2026-03-28)
- **Autonomous Execution**: Run nonstop, minimize Eric interruptions. Only pause for: money, external comms, genuine ambiguity, security.
- **Correctness-First**: Output correctness > completeness > visible failures > root causes > speed
- **Output Parity**: All delivery channels (email, download, API) serve identical content, SHA256-verified
- **RCA Core**: Root cause analysis is step 1 of debugging, not post-mortem

## PowerSpec Rebuild (2026-04-01)
- OS crashed connecting Dell 6K monitor — fresh Windows 11 installed on new NVMe
- Full rebuild completed in ~2 hours via Tailscale + SSH from MacBook
- **Rebuild guide:** `memory/powerspec-rebuild-guide.md` — comprehensive step-by-step reference
- **Key lesson:** ASRock Z790-C has NO built-in Windows drivers for LAN or WiFi — must load from old NVMe DriverStore or USB
- **Driver paths on old drive:** `D:\Windows\System32\DriverStore\FileRepository\e1d.inf_*` (LAN) and `e2xw10x64.inf_*` (WiFi)
- **New Tailscale:** hostname `powerspecpc`, IP `100.81.21.114` (was `remote-coder-main` / `100.67.128.123`)
- **New SSH user:** "Eric Brown" with space (was `ericf`) — must quote in commands
- **Docker credential fix:** Renamed desktop/wincred helpers, set credsStore="" (SSH can't access Windows Credential Manager)
- **10 containers restored:** FinancialReportApp (5) + ContractAnalyzer (5)
- **Old drive accessible at D:** — has previous configs, .env files, project files at D:\Users\ericf\

## Dell U5226KW 6K Monitor
- Model: Dell UltraSharp U5226KW — 52" curved, 6K (6144x2560), 120Hz, 21:9
- Connection: DisplayPort 1.4 with DSC from RTX 5080 (UGREEN DP 2.1 cable ordered)
- **CRITICAL:** Previous connection attempt crashed Windows — use cold-plug procedure only
- Cold-plug: Shut down PC → connect cable → turn on monitor → wait 5s → power on PC
- Start at 60Hz, then increase to 120Hz once stable
- Inputs available: 2x HDMI 2.1, 2x DisplayPort 1.4, 1x Thunderbolt 4, 3x USB-C upstream
- Built-in: KVM switch, 2.5GbE Ethernet, USB hub, 2x9W speakers

## Project Ajax — Jarvis NemoClaw Migration (2026-04-12)
- **What:** New dedicated AI server, to be deployed inside Cohesity network
- **Hardware:** 1TB total RAM, dual NVIDIA 6000-series GPUs
- **Platform:** NemoClaw (NVIDIA's enterprise AI agent framework, built on OpenClaw)
- **Codename:** Project Ajax — named after HMS Ajax, British cruiser at Battle of the River Plate (1939)
- **Purpose:** Production-grade Jarvis with enterprise security, SOC 2, 5x throughput, 1M context window
- **Key NemoClaw advantages:** OpenShell containerized sandboxing, cryptographic skill signing, native Salesforce/ServiceNow/SAP connectors, 1M token context vs OpenClaw's 200K
- **NemoClaw NOT:** not a replacement for OpenClaw — it's an upgrade layer. Skills and config are portable.
- **Migration plan:** snapshot MacBook Jarvis → clone to Ajax → stand up Jarvis NemoClaw V1.0
- **Plan file:** `plans/cic-command-information-center.md` Phase 5 section
- **Tasks:** `project-ajax` in tasks.json
- **Status:** Hardware ordered — plan ready, waiting for hardware arrival
- **Key questions pending:** Linux distro choice, Tailscale vs Cohesity IP, run mode (primary vs parallel), NemoClaw license via Cohesity

## CIC — Command Information Center (2026-04-12)
- **What:** Live force-directed entity graph of entire Jarvis SDLC in Mission Control
- **New tab:** "CIC" in Mission Control sidebar (Radar icon)
- **Tech:** Python parser (parse_sdlc.py) → graph_data.json → Cytoscape.js
- **Also:** populates Obsidian EricBrain/JarvisSDLC/ vault for native Obsidian graph view
- **Auto-update:** fires on every Dropbox backup
- **Plan file:** `plans/cic-command-information-center.md`
- **V1 target:** 2026-04-12 morning
- **Vault:** EricBrain with /JarvisSDLC/ subfolder (pending Eric confirmation)

## Project Ajax — Configuration Details (2026-04-12)
- **NemoClaw license:** Corporate NVIDIA agreement (Kathir Nagireddy handles procurement/IT)
- **IT contact:** Kathir Nagireddy — primary contact for AD join, firewall rules, MCP credentials, developer SSH access
- **Claude API:** Corporate Claude API key (not personal) — configure via Cohesity enterprise account
- **Kathir SSH access:** Scope TBD — Kathir is also IT contact, project scope to be defined once hardware arrives
- **CEO block (hardcoded):** sanjay.poonen@cohesity.com — PERMANENTLY blocked from all Ajax scanning/access
- **Log retention:** 12 months for all AI action logs
- **Slack access:** Via Eric's user access token + Cohesity corporate Slack MCP server
- **Core platform rule:** Claude + MCP servers is the primary stack for everything on Ajax — not raw API calls, not custom connectors
- **No OpenAI / no Grok on Ajax** — Claude is the exclusive LLM, MCP is the integration layer

## Project Ajax — LLM Stack (2026-04-12)
- **All API keys available on Ajax:** Anthropic (Claude), xAI (Grok), OpenAI — full multi-model stack
- **Model tiering preserved exactly** from current OpenClaw setup — same agent→model assignments
- **NemoClaw does NOT replace the LLM stack** — it's the sandbox/security layer only; Claude/Grok/OpenAI route through it unchanged
- **Critical:** When migrating to NemoClaw, unset ANTHROPIC_API_KEY from shell environment (NemoClaw conflict); inject it via OpenShell provider config instead
- **openclaw.json model config migrates as-is** — all agent model assignments carry over
