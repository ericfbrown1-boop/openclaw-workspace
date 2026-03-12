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

## GPT 5.4 Trial (Started 2026-03-11)
- Eric approved trial of GPT 5.4 (openai/gpt-5.1-codex) for subagent work
- Primary use: Cross-review loop for Planner output (dual-model architecture review)
- Inspired by Alex Finn's recommendation (switched from Opus to 5.4 for speed)
- Jarvis main model stays Opus 4.6 — GPT 5.4 is a reviewer/second opinion
- Pipeline: Planner drafts → GPT 5.4 reviews → Jarvis decides what to incorporate
- Trial period: 2 weeks, evaluate by 2026-03-25
- For routine subagent tasks, can use GPT 5.4 where speed > depth

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
