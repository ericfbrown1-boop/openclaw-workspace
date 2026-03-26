# Changelog

All notable changes to OpenClaw workspace are documented here.

## [2026-03-25] - Best Practices Upgrade (Full Day Session)
### Added
- CLAUDE.md, CHANGELOG.md, AUTH_FALLBACKS.md, DISPATCH_TEMPLATE.md
- 8 Cohesity domain skills implemented (earnings-analyzer, competitive-intel, financial-report-gen, cohesity-domain, snowflake-sql, slack-teams-hub, tax-automation, workday-analytics)
- Salesforce analytics full implementation (SKILL.md + IMPLEMENTATION.md)
- GitHub Actions CI/CD (.github/workflows/ci.yml)
- Pre-commit hooks (.pre-commit-config.yaml: ruff, shellcheck, detect-secrets)
- Test oracle schemas (skills/auditor/TEST_ORACLES.md — 8 oracle types)
- Per-project CLAUDE.md (ProjectScraper, folder-monitor, stock-ticker)
- Monitor Step 4.5: Tailscale health check
- Monitor Step 11: 4-phase workflow compliance enforcement
- Dual-write rule for tasks.json (workspace + Mission Control)
- PowerSpec as visible agent on Mission Control dashboard
- Coding workflow guide (documents/OpenClaw_Coding_Workflow_Guide.md)
- Stability fix plan (plans/stability-fix-plan.md)
- Security hardening tracker (plans/security-hardening.md)
- GPT-5.4 upgrade plan (plans/planner-gpt54-upgrade.md)

### Changed
- PIPELINE.md: explicit 4-phase labels, model tiering with costs, E2E verification checklist
- DELEGATION.md: Conductor dual-write rule, updated dispatch rules
- Monitor SKILL.md: Tailscale check, 4-phase enforcement, dual-write sync, Telegram reduced to hourly
- POWERSPEC.md: Docker GPU commands, PyTorch nightly note, critical notes
- KNOWN_FAILURES.md: 3 new patterns (context chunking, bot detection, PowerShell TLS)
- Salesforce SKILL.md split from 38KB to 12KB + 27KB IMPLEMENTATION.md

### Fixed
- 55 bare `except:` → `except Exception:` across 20 Python files
- SIGTERM graceful restarts no longer count as outages on Health dashboard (84.6% → ~99.9%)
- Anthropic research task synced to Mission Control (was showing stale 25%)
- Next.js rebuild step documented (pm2 restart alone serves stale code)

### Removed
- 13 junk files (clawdbot dupes, UUID temps, completion markers, .bak)
- 3 German language output files
- Root-level duplicates (GPT54, IDE_Summary .docx/.txt)

### Organized
- 162 root files moved to scripts/legacy/, data/, documents/, data/images/
- 35 output .md files moved to documents/
- Root reduced from 232 to 36 files
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

## [2026-03-06] - System Security Audit
### Assessed
- Full workspace security audit (3 CRITICAL, 4 warnings, 6 housekeeping)
- Disk usage baseline: 414 MB workspace, 44 MB logs, 230 MB orphaned venvs
- Cron health review: 2 ERROR state jobs (Daily Tax Email Scan, Clawdbot Data Refresh)
- LaunchAgent verification: 6 plists properly configured
### References
- references/OpenClaw_System_Audit_2026-03-06.docx

## [2026-03-05] - Morning Session: Remote Coder + ProjectScraper
### Added
- Remote Coder iPhone access via Tailscale (self-signed cert + iOS profile)
- ProjectScraper first Rubrik competitive intel crawl (17 URLs)
- Tailscale tailnet: 3 devices connected (Mac, PC, iPhone)
### Learned
- Context window chunking: process 1 URL at a time, not 17
- Bot detection mitigation: 3-second delays between requests
- PowerShell 5.x vs 7.x TLS incompatibility on Windows SSH
### References
- references/Morning_Session_Recap_EricBrown.docx

## [2026-03-04] - PowerSpec GPU Environment Build
### Added
- Full GPU dev environment: Windows 11 → WSL2 → Docker → RTX 5080
- PyTorch nightly (cu128) for Blackwell architecture (sm_120)
- VS Code Dev Containers with GPU passthrough (--gpus all)
- Remote Coder initial setup (10 bootstrap problems solved)
- GitHub SSH auth inside Docker containers
- Benchmark: 8192x8192 matrix multiply in 79.4ms (~13 TFLOPS)
### References
- references/Remote_Session_Recap_EricBrown.docx
- references/IDE_Summary_EricBrown.docx
