# OpenClaw Workspace — Claude Code Instructions

## Quick Start
Read these files in order before doing anything:
1. `SOUL.md` — Agent identity and values
2. `USER.md` — About Eric (CFO & COO, Cohesity)
3. `AGENTS.md` — Session bootstrap and workspace rules
4. `DELEGATION.md` — Agent routing (9 agents)
5. `PIPELINE.md` — Code pipeline and completion gates
6. `POWERSPEC.md` — Compute allocation (MacBook vs PowerSpec)

## Build & Test
- All code defaults to Docker + Railway deployment
- See `skills/railway-deployment/SKILL.md` for standards
- Run tests before every commit
- PowerSpec (100.67.128.123) for heavy compute

## Auth
- Google: `gog` CLI (OAuth via macOS Keychain)
- GitHub: `gh` CLI
- If auth fails: see `skills/google-oauth-reauth/SKILL.md`
- Check `memory/auth-fallback-state.json` for fallback mode status

## Key Rules
- NEVER delete Eric's files
- Always CC ericfbrown1@gmail.com on sent emails
- Check `memory/cron-state.json` before running any cron task
- Log all failures to `memory/incidents.jsonl`
- Check `memory/api-usage-state.json` before Opus tasks (downgrade to Sonnet if >75% budget)
