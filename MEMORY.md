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

## Google Sheets / Drive
- gog CLI configured with ericfbrown1@gmail.com
- Services: gmail, calendar, contacts, drive, docs, sheets
- Google Sheets API and Drive API both enabled (project 672907822296)

## Hong Kong Trip
- March 11-13, 2026, Hong Kong Island
- Wants harbor view room
- Top picks: Four Seasons (Central/IFC), Mandarin Oriental, Conrad, Island Shangri-La, Upper House

## CGT (Chateau Grand Traverse) — Pricing Issue
- Email from Eddie (Feb 2026): claims $8,496.15 overpayment 2024-2025 due to Pinot Gris Brix base error (19° vs contracted 22°)
- CGT proposes credit $8,496.15 to 2026 + price increase ($1,725→$1,750/ton, PG Brix base 22°→21°)
- CONTRACT IN DROPBOX — need to verify 22.0° Brix is indeed the contracted PG base
- Dropbox token expired as of Feb 26, 2026 — Eric needs to refresh

## Dropbox
- Eric's personal Dropbox token EXPIRED Feb 26, 2026
- Refresh at dropbox.com/developers

## Identity
- Name: Jarvis
- First established: 2026-02-07
- Memory wiped at some point, reconnected ~2026-02-23
