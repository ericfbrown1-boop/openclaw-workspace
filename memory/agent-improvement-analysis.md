# Agent System Self-Improvement Analysis
**Date:** 2026-03-17 | **Analyst:** Jarvis (Opus 4.6)
**Scope:** Agents 1-7 (Jarvis, Researcher, Planner, Coder, Quality, Auditor, Conductor)
**Evidence base:** 7 days of sessions, GitHub commits, Railway logs, memory files, KNOWN_FAILURES.md

---

## EVIDENCE GATHERED

### Incident 1: ContractAnalyzer Railway Deployment Disaster (Mar 16)
**15 consecutive fix commits in 90 minutes** (4:17 AM - 5:27 AM):
1. Fix Dockerfile to reference api subdirectory
2. Update railway.json to use root Dockerfile
3. Fix Dockerfile - single line RUN command
4. Fix railway.json to use root Dockerfile and correct PORT variable
5. Remove hardcoded CMD - use startCommand from railway.json
6. Escape PORT variable in startCommand
7. Fix: add CMD to Dockerfile for Railway deployment
8. Fix: use sh -c for PORT variable expansion
9. Fix: remove railway.json, fix Dockerfile CMD with sh -c
10. Fix: correct module path to app.main:app
11. Fix: separate pgvector extension and create_all into distinct transactions
12. Fix: force fresh Railway build
13. Fix: add .env to gitignore
14. Fix: add broker_connection_retry_on_startup to celery config

**Root cause analysis:**
- Coder agent didn't follow Docker-first standard despite it being in AGENTS.md
- No pre-deployment Docker build verification happened locally
- Railway Agent interference wasn't detected early
- railway.json and Dockerfile conflicted with each other
- $PORT variable expansion wasn't tested
- Module path was wrong (should have been caught by import verification)
- Database initialization crashed (pgvector extension vs create_all ordering)
- Celery broker connection not configured for Railway's startup timing
- .env was committed to repo (security issue caught late)

### Incident 2: OAuth/Auth Cascade Failure (Mar 13)
**7 briefing attempts** from 1:48 AM to 6:00 AM because:
- gog CLI OAuth token expired/locked behind keychain
- gh CLI token expired (401)
- himalaya IMAP credentials expired
- **All three credential paths failed simultaneously**
- Gateway entered restart loop (13+ LLM timeouts, cycling every 10 min)
- No fallback path besides Telegram existed

### Incident 3: Daily Briefing Cron Storm (Mar 13)
- Cron triggered 7 times for the same briefing
- Each run spawned a new isolated session
- No deduplication or "already ran successfully" logic
- Wasted significant tokens across 7 runs
- Eventually self-resolved when Mar 16 briefing succeeded normally

### Incident 4: Tailscale CLI Conflict (Mar 17)
- Homebrew and Mac App Store tailscale both installed
- CLI path confusion caused `tailscale status` to fail intermittently
- Not caught by any agent until manual debugging session with Eric
- Required manual fix (brew uninstall tailscale)

### Incident 5: Import Errors in Coder Output (Ongoing)
- KNOWN_FAILURES.md documents ~25% of Coder tasks have import errors
- Pre-commit checklist exists but isn't enforced
- Quality agent catches these, but the round-trip wastes time

### Incident 6: PIPELINE_STATE.json Never Used
- Created Mar 11 as a "quick win" but template is empty
- No pipeline has been tracked through it
- Coder doesn't update it, Jarvis doesn't read it

---

## GAP ANALYSIS BY AGENT

### 1. Jarvis (Orchestrator)
**Gaps found:**
- G1.1: No circuit breaker for cron storms — same briefing ran 7x
- G1.2: No auth health pre-check before dispatching work that needs Google/GitHub
- G1.3: PIPELINE_STATE.json is dead code — never reads or updates it
- G1.4: No error classification before dispatching to Quality (sends raw errors)
- G1.5: No "deployment readiness gate" — dispatches to Conductor without verifying Docker builds locally first
- G1.6: No token spend tracking per pipeline run

### 2. Researcher (Oracle)
**Gaps found:**
- G2.1: No Railway/deployment-specific research capability documented
- G2.2: No "pre-flight research" phase for common deployment failures (would have caught pgvector, Celery broker issues)
- G2.3: AGENTS.md is only 89 lines — much thinner than other agents
- G2.4: No structured output format for different research types (financial vs technical vs competitive)
- G2.5: No caching/dedup awareness — researches the same topics repeatedly across sessions

### 3. Planner (Architect)
**Gaps found:**
- G3.1: Edge Case Checklist exists but doesn't include database initialization ordering (pgvector before create_all)
- G3.2: No "Railway deployment verification tasks" in the standard task breakdown
- G3.3: Doesn't plan for credential/auth failure modes in infrastructure design
- G3.4: No local Docker build verification step in the plan template
- G3.5: Missing "pre-deploy smoke test" task that runs BEFORE pushing to Railway
- G3.6: 350 lines is comprehensive but Edge Case Checklist needs expansion

### 4. Coder (Scotty)
**Gaps found:**
- G4.1: Pre-commit checklist isn't enforced — import verification skipped in ContractAnalyzer
- G4.2: No local Docker build step before pushing to GitHub
- G4.3: Module path verification not tested (app.main:app was wrong)
- G4.4: No database initialization testing (pgvector extension ordering)
- G4.5: .env was committed despite .gitignore rules being documented
- G4.6: Celery/worker configuration not tested with Railway's startup timing
- G4.7: PORT variable expansion not tested before deployment
- G4.8: 15 fix commits = 15 push-test-fail-fix cycles — no local verification
- G4.9: CHECKPOINT.md and HANDOFF.md protocols exist but evidence of actual use is minimal

### 5. Quality (Inspector)
**Gaps found:**
- G5.1: Security audit Part B didn't catch .env committed to repo before deployment
- G5.2: No "deployment readiness" audit phase (Dockerfile correctness, PORT binding, module paths)
- G5.3: Part C Code Quality doesn't check database initialization patterns
- G5.4: No "Railway-specific" checklist (worker config, broker timing, pgvector ordering)
- G5.5: 397 lines is thorough for security but weak on deployment verification
- G5.6: Doesn't verify CHECKPOINT.md/HANDOFF.md were actually written by Coder

### 6. Auditor (External)
**Gaps found:**
- G6.1: Only 87 lines — very thin
- G6.2: No pre-packaging verification (does the app actually run?)
- G6.3: Doesn't check deployment status before offering Grok review
- G6.4: No structured feedback loop from Grok review back into the pipeline
- G6.5: Doesn't verify Quality audit actually passed before running

### 7. Conductor
**Gaps found:**
- G7.1: No local Docker build verification BEFORE pushing to Railway
- G7.2: No staged deployment (local Docker → Railway staging → production)
- G7.3: Doesn't check for common Railway-specific failures BEFORE deploying
- G7.4: No rollback automation (just "check SKILL.md Section X")
- G7.5: Preflight check is mentioned in pipeline but not documented in AGENTS.md
- G7.6: Doesn't verify auth credentials are working before deploying apps that need them

---

## CROSS-CUTTING ISSUES

### C1: The "15 Fix Commits" Problem
The entire agent system failed to prevent 15 iterative fix commits. The root cause: **no local verification before remote deployment**. Every agent has documentation about Docker-first, but no agent enforces a mandatory `docker build && docker run && curl localhost:PORT/health` step.

### C2: Auth Credential Fragility
Three auth systems failed simultaneously (Google OAuth, GitHub, IMAP). No agent is responsible for credential health monitoring. The smoke test now covers this, but agents still dispatch work without checking if credentials are healthy.

### C3: Cron Deduplication
The briefing cron ran 7 times because there's no "already succeeded" check. Jarvis's AGENTS.md doesn't mention cron idempotency.

### C4: PIPELINE_STATE.json Is Dead Code
Created as a quick win but never integrated into any agent's workflow. Either integrate it or remove it.

### C5: Agent Protocols Are Documented But Not Verified
CHECKPOINT.md, HANDOFF.md, pre-commit checklists — these exist in docs but there's no enforcement mechanism. When under pressure, agents skip them.

---

## PROPOSED CHANGES (for Grok cross-review)

### Jarvis Changes:
1. Add auth health pre-check before dispatching credential-dependent work
2. Add cron deduplication logic (check last successful run before re-running)
3. Either integrate PIPELINE_STATE.json or remove it
4. Add deployment readiness gate (require local Docker verification before Conductor)
5. Add error classification system before sending to Quality

### Researcher Changes:
1. Add structured output templates for different research types
2. Add "deployment pre-flight research" capability for Railway-specific issues
3. Expand from 89 to ~150 lines with better structure
4. Add research caching awareness

### Planner Changes:
1. Expand Edge Case Checklist with database initialization, service ordering, auth failures
2. Add mandatory "local Docker verification" task to every plan
3. Add "pre-deploy smoke test" task template
4. Add Railway-specific failure mode awareness

### Coder Changes:
1. Make pre-commit checklist MANDATORY with enforcement language
2. Add `docker build && docker run` as required step before any git push
3. Add PORT variable expansion verification step
4. Add database initialization testing (CREATE EXTENSION before CREATE TABLE)
5. Add .gitignore verification as first step of every project
6. Reduce "fix commit" rate target: max 3 fix commits per deployment

### Quality Changes:
1. Add Part D: Deployment Readiness Audit (Dockerfile, PORT, module path, env vars, DB init)
2. Add verification that Coder actually wrote CHECKPOINT.md/HANDOFF.md
3. Add Railway-specific deployment checklist
4. Verify .env is in .gitignore before security audit

### Auditor Changes:
1. Verify deployment is actually running before offering Grok review
2. Add structured feedback template for Grok review results
3. Verify Quality audit actually passed
4. Expand to ~120 lines with clearer process

### Conductor Changes:
1. Add mandatory local Docker build + run before Railway push
2. Add staged deployment: local → verify → Railway
3. Add credential verification before deploying credential-dependent apps
4. Add automated rollback commands (not just "check SKILL.md")
5. Document the preflight check process explicitly
