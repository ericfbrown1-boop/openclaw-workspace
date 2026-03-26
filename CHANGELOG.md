# Changelog

All notable changes to OpenClaw workspace are documented here.

## [2026-03-25] - Best Practices Upgrade
### Added
- CLAUDE.md for Claude Code native integration
- CHANGELOG.md for tracking workspace changes
- 9 Cohesity domain skill skeletons (earnings-analyzer, competitive-intel, financial-report-gen, salesforce-analytics, snowflake-sql, slack-teams-hub, tax-automation, workday-analytics, cohesity-domain)
- Stability fix plan (plans/stability-fix-plan.md)
- Auth circuit breaker + auto-fallback to Zapier MCP
- API credit monitoring (scripts/api_usage_monitor.py)
- Token refresh wrapper (scripts/gog_token_refresh.sh)
- Battery guard + gateway heartbeat scripts
- Anthropic best practices alignment audit

### Changed
- selfheal.sh — added OAuth health check, usage tracking, circuit breaker
- daily_smoketest.sh — added API usage section
- PIPELINE.md — added cost gates
- DELEGATION.md — updated dispatch rules
- monitor/SKILL.md — added auto-fallback instructions
- AGENTS.md — updated cron deduplication with auth circuit breaker

## [2026-03-24] - SDLC Overhaul
### Added
- Split AGENTS.md into focused companion files (DELEGATION.md, PIPELINE.md, POWERSPEC.md, INCIDENTS.md)
- External Auditor daily vibe coding vulnerability scan
- Weekly Claude best practices audit
- Monitor subagent watchdog (auto-restart stuck agents)
- Zero Idle rule

## [2026-03-23] - Multi-Agent Pipeline v2
### Added
- 9-agent pipeline (Planner, Researcher, Coder, Tester, Quality, Auditor, Conductor, Monitor, Librarian)
- Mission Control dashboard (JarvisMissionControl)
- PowerSpec hybrid compute integration
- Incident-driven learning loop (INCIDENTS.md)
