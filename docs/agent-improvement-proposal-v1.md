# Agent System Improvement Proposal v1
**Date:** 2026-03-17 | **Reviewed by:** Opus 4.6 + Grok 4
**Status:** PENDING ERIC'S APPROVAL

---

## Executive Summary

Analyzed 7 days of sessions, 15 fix commits on ContractAnalyzer, an OAuth cascade failure, cron storms, and ongoing 25% import error rate. Found **32 gaps** across 7 agents. Grok confirmed most proposals, flagged 4 as wrong/unnecessary, and added 5 missed gaps.

**The core problem:** We document the right processes but don't enforce them. Under pressure, agents skip checklists.

**New capability:** Windows 11 remote coding PC (remote-coder-main) integrated into the pipeline for heavy-duty Docker builds, GPU workloads, and large codebase operations via Tailscale SSH.

---

## FINAL CHANGES BY AGENT

Priority ratings: 🔴 CRITICAL (prevents known failures) | 🟡 IMPORTANT (significant improvement) | 🟢 NICE-TO-HAVE

---

### AGENT 1: 🤖 Jarvis — Orchestrator
**File:** `~/.openclaw/workspace/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| J1 | **Add auth health pre-check rule:** Before dispatching any work that needs Google/GitHub/IMAP, run `gog gmail search "newer_than:1h" --max 1` and `gh auth status` first. If either fails, notify Eric and use fallback paths (Zapier MCP, Telegram). | 🔴 | Mar 13: 7 failed briefings because auth was dead |
| J2 | **Add cron deduplication rule:** Before running any cron task, check if the same cron ID has a successful completion in the last 4 hours. If yes, skip with HEARTBEAT_OK. Write last-success timestamp to `memory/cron-state.json`. | 🔴 | Mar 13: Same briefing ran 7 times |
| J3 | **Add deployment readiness gate:** Before dispatching to Conductor, require Coder to confirm: (a) `docker build .` succeeds, (b) `docker run` + `curl localhost:PORT/health` passes, (c) HANDOFF.md exists. If any missing, send back to Coder. | 🔴 | Mar 16: 15 fix commits because no local verification |
| J4 | **Remove PIPELINE_STATE.json** (dead code) and its references. Replace with a simpler rule: Jarvis tracks pipeline stage in the conversation context itself, not a JSON file that nobody reads. | 🟡 | Created Mar 11, never used |
| J5 | **Add error classification before Quality dispatch:** Classify errors into categories (import, auth, Docker, Railway, database, other) and include category + relevant KNOWN_FAILURES.md entry in the dispatch message to Quality. | 🟡 | Quality gets raw errors with no context |
| J6 | **Add centralized incident tracking:** When any agent encounters a failure, log it to `memory/incidents.jsonl` with timestamp, agent, error category, resolution. Review weekly for patterns. | 🟡 | Grok flagged: no cross-agent error tracking |
| J7 | **Add Windows remote coding routing rules:** When a project meets ANY of these criteria, route Coder to execute on remote-coder-main (100.67.128.123) via SSH over Tailscale instead of locally on the MacBook: (a) Project requires GPU (ML, CUDA, AI model inference) (b) Docker build exceeds 5 minutes or image > 2GB (c) Codebase > 50K lines or requires > 16GB RAM (d) Project uses GPU-accelerated libraries (PyTorch, TensorFlow, RAPIDS) (e) Eric explicitly requests "heavy" or "remote" execution. For all other projects, default to MacBook. Jarvis must verify `tailscale ping remote-coder-main` succeeds before dispatching remote work. If unreachable, fall back to MacBook and notify Eric. | 🔴 | New capability: 128GB RAM + RTX 5080 GPU available for heavy workloads |

**Lines added: ~60 | Total after: ~426**

---

### AGENT 2: 🔬 Oracle — Researcher
**File:** `~/.openclaw/workspace-researcher/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| R1 | **Add structured output templates** for 3 research types: (a) Financial Analysis — revenue table, growth rates, valuation multiples, competitive positioning (b) Technical Evaluation — compatibility matrix, Docker/Railway readiness, license, maintenance status (c) Competitive Intel — market share, product gaps, vulnerability disclosures, pricing | 🟡 | No standard format; downstream agents get inconsistent outputs |
| R2 | **Add Railway/infrastructure research section:** When researching libraries or frameworks, always include: Docker base image compatibility, known Railway issues, env var requirements, startup time considerations. Add to existing "Output for Planner" section. | 🟡 | Mar 16: pgvector + Celery broker timing would have been caught |
| R3 | **Add KNOWN_FAILURES.md consultation rule:** Before researching an error topic, read `KNOWN_FAILURES.md` first. If the pattern is already documented, cite it and focus research on new aspects only. | 🟡 | Avoids redundant research on known problems |
| R4 | **Add GPU/Windows research awareness:** When evaluating libraries for GPU-heavy projects, include: CUDA version compatibility, Windows vs Linux Docker behavior, WSL2 GPU passthrough requirements, NVIDIA Container Toolkit setup. Note whether the library runs natively on Windows or requires WSL2. | 🟡 | New: GPU workloads will run on Windows PC |

**Lines added: ~60 | Total after: ~149**

---

### AGENT 3: 📐 Architect — Planner
**File:** `~/.openclaw/workspace-planner/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| P1 | **Expand Edge Case Checklist** — add 5 new items to the existing 10: (11) Database extension/migration ordering — CREATE EXTENSION before CREATE TABLE (12) Service startup ordering — broker must be ready before workers connect (13) Auth token expiry during long-running operations (14) railway.json vs Dockerfile CMD conflicts — use ONE, not both (15) .env and secrets — verify .gitignore BEFORE first commit | 🔴 | Mar 16: Items 11, 12, 14, 15 all caused failures |
| P2 | **Add mandatory "Local Docker Verification" task** to Phase 3 of every plan template. Task reads: "Build and run Docker container locally. Verify: (a) `docker build -t project .` succeeds, (b) `docker run -p 8000:8000 project` starts without errors, (c) `curl localhost:8000/health` returns 200. If Docker Desktop not installed, document as blocker." | 🔴 | Mar 16: No local verification = 15 fix commits |
| P3 | **Add "Pre-Deploy Smoke Test" task** between Tester and Conductor phases: "Run all API endpoints against local Docker container. Verify database migrations, worker connections, and auth flows work inside the container — not just on bare metal." | 🟡 | Would have caught pgvector + Celery broker issues |
| P4 | **Add credential/auth failure planning** to Risk Assessment template: "For every external service (Google APIs, GitHub, database, Redis, S3), document: what happens if auth fails at runtime? What's the fallback? What's the alert mechanism?" | 🟡 | Mar 13: No auth failure planning = 7 failed briefings |
| P5 | **Add execution environment selection to every PLAN.md.** New required section: `## Execution Environment` with decision: MacBook (light, standard Docker, no GPU) vs Windows PC remote-coder-main (heavy Docker builds, GPU/CUDA, large codebases, 128GB RAM). Selection criteria table: project size, GPU requirement, estimated build time, RAM needs. If Windows PC selected, plan must include: SSH connectivity verification task, docker-compose.gpu.yml for GPU passthrough, and a note that Tailscale must be online. | 🔴 | New: routing heavy vs light work to the right machine |

**Lines added: ~50 | Total after: ~400**

---

### AGENT 4: ⚙️ Scotty — Coder
**File:** `~/.openclaw/workspace-coder/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| C1 | **Upgrade pre-commit checklist from "should do" to MANDATORY GATE.** Change header to: `## 🚫 MANDATORY Pre-Commit Gate (DO NOT SKIP)`. Add: "If ANY check fails, DO NOT commit. DO NOT push. Fix the issue first. Skipping this gate is a pipeline violation that will be caught by Quality and sent back." | 🔴 | 25% import error rate proves current language is too soft |
| C2 | **Add Docker verification as commit gate item:** Before any `git push`, run: (a) `docker build -t project .` — must succeed (b) `docker run -d -p 8000:8000 --env-file .env.example project` — must start (c) `curl -f http://localhost:8000/health` — must return 200 (d) `docker stop` + cleanup. If Docker Desktop not available, write "DOCKER NOT VERIFIED" in HANDOFF.md (Conductor will do it). | 🔴 | Mar 16: Zero local Docker verification |
| C3 | **Add .gitignore-first rule:** "The FIRST file you create or verify in ANY project is `.gitignore`. Before writing any code, confirm `.gitignore` contains: `.env`, `.env.*`, `*.pyc`, `__pycache__/`, `node_modules/`, `*.pem`, `*.key`. Run `git status` to verify no sensitive files are tracked." | 🔴 | Mar 16: .env was committed to ContractAnalyzer |
| C4 | **Add PORT variable expansion test:** "After writing Dockerfile CMD, test it locally: `docker build -t test . && PORT=8000 docker run -e PORT=8000 -p 8000:8000 test`. Verify the app actually binds to the PORT value, not a literal string `$PORT`." | 🟡 | Mar 16: 3 commits just fixing PORT expansion |
| C5 | **Add database initialization ordering rule:** "When using SQLAlchemy + PostgreSQL extensions (pgvector, PostGIS, etc.): ALWAYS run `CREATE EXTENSION IF NOT EXISTS` in a separate transaction BEFORE `Base.metadata.create_all()`. Never combine them in the same transaction block." | 🟡 | Mar 16: pgvector vs create_all ordering crash |
| C6 | **Add Celery/worker startup rule:** "When configuring Celery for Railway: always set `broker_connection_retry_on_startup=True` in Celery config. Railway services start in parallel — the broker (Redis) may not be ready when the worker starts." | 🟡 | Mar 16: Celery crash on Railway startup |
| C7 | **Add railway.json vs Dockerfile conflict rule:** "Use ONLY the Dockerfile CMD for startup commands. Do NOT use railway.json `startCommand` — it conflicts with and overrides the Dockerfile CMD unpredictably. If railway.json exists, it should contain ONLY build settings (builder, buildCommand), NOT runtime settings." | 🟡 | Mar 16: 4 commits fighting this conflict |
| C8 | **Add Windows Remote Execution Protocol.** New section: `## 🖥️ Remote Execution on Windows PC (remote-coder-main)`. When Jarvis dispatches work to the Windows PC, Coder operates via SSH over Tailscale: (a) **Connect:** `ssh ericbrown@100.67.128.123` (b) **Verify environment:** `docker --version && git --version && nvidia-smi` (c) **Clone/pull repo:** `git clone <repo>` or `cd <project> && git pull` (d) **Docker builds:** Run `docker build` and `docker-compose up` on the Windows PC — it has Docker Desktop with NVIDIA GPU support (e) **GPU workloads:** Use `docker-compose.gpu.yml` with `runtime: nvidia` and `NVIDIA_VISIBLE_DEVICES=all` for CUDA tasks (f) **Push to GitHub:** Commit and push directly from Windows — git is configured with Eric's credentials (g) **Health check:** After Docker runs, test endpoints from the Mac: `curl -f http://100.67.128.123:PORT/health` (h) **Cleanup:** Stop containers and clean up after task completion. **Key rules:** Always verify Tailscale connectivity first (`tailscale ping remote-coder-main`). Never store secrets on the Windows PC — use env vars passed at runtime. Write CHECKPOINT.md to the project directory on Windows (same protocol as local work). All HANDOFF.md files must be readable from both Mac and Windows (use the git repo as shared state). | 🔴 | New: Enables heavy-duty Docker builds and GPU workloads |

**Lines added: ~100 | Total after: ~401**

---

### AGENT 5: 🔍 Inspector — Quality
**File:** `~/.openclaw/workspace-quality/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| Q1 | **Add Part D: Deployment Readiness Audit.** New section that runs before Conductor gets the code. Checks: (a) Dockerfile exists and has valid CMD with `sh -c` for variable expansion (b) `$PORT` or `${PORT:-8000}` used correctly (not literal `$PORT` in exec form) (c) Module path in uvicorn command matches actual file structure (d) `.env` is NOT tracked by git (`git ls-files .env` returns empty) (e) `.gitignore` includes `.env`, `.env.*` (f) `requirements.txt` / `package.json` includes ALL imported packages (g) Database migrations/extensions are ordered correctly (h) Health endpoint exists at the documented path | 🔴 | Mar 16: ALL of these would have caught ContractAnalyzer issues |
| Q2 | **Add Railway-specific deployment checklist** to Part D: (a) No `railway.json` startCommand (conflicts with Dockerfile CMD) (b) `broker_connection_retry_on_startup=True` if Celery is used (c) All env vars documented in `.env.example` (d) No hardcoded `localhost` database URLs (e) `HEALTHCHECK` instruction in Dockerfile matches the actual health endpoint | 🔴 | Mar 16: Railway-specific failures not covered |
| Q3 | **Add Coder compliance verification** to start of every review: "Before starting Parts A-D, verify Coder wrote: (a) HANDOFF.md — if missing, flag as 🟡 WARNING and request (b) CHECKPOINT.md — if task was >5 minutes and missing, flag as 🟡 WARNING. Note compliance status in your report header." | 🟡 | HANDOFF/CHECKPOINT protocols exist but aren't verified |
| Q4 | **Add .env/secrets check as Phase 0** of Part B Security Audit: "BEFORE running the full 6-phase security scan, do a quick pre-flight: `git ls-files | grep -E '\.env$\|\.env\.'`. If any .env files are tracked, flag as 🔴 CRITICAL immediately — do not wait for full audit." | 🟡 | Mar 16: .env committed and not caught until late |
| Q5 | **Add remote execution audit checks.** When code was built/tested on the Windows PC: (a) Verify no Windows-specific paths leaked into code (e.g., `C:\Users\`, backslash paths) (b) Verify no secrets were left on the Windows PC filesystem (c) Verify Docker images built on Windows also build on Linux (Railway runs Linux containers) (d) Verify GPU-specific code has graceful fallback when no GPU is available (e) Check that `docker-compose.gpu.yml` doesn't accidentally become the default `docker-compose.yml` in the repo | 🟡 | New: Windows-built code needs cross-platform validation |

**Lines added: ~85 | Total after: ~482**

---

### AGENT 6: 🛡️ External Auditor
**File:** `~/.openclaw/workspace-auditor/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| A1 | **Add Quality audit verification gate:** "Before Step 1, confirm Quality Agent has completed Parts B + D (Security + Deployment Readiness). Request the audit report from Jarvis. If Quality hasn't run or reported 🔴 CRITICAL findings, STOP and notify Jarvis — do not proceed to packaging." | 🔴 | No verification that Quality actually passed |
| A2 | **Add deployment health verification:** "Before offering Grok review, verify the app is actually deployed and healthy: `curl -f https://APP.up.railway.app/health`. If it returns an error or 502, notify Jarvis — the code isn't ready for external review." | 🟡 | Could offer review of non-working code |
| A3 | **Add structured Grok review feedback capture:** "If Eric approves Grok review and provides feedback, save it to `PROJECT_DIR/GROK_REVIEW.md` with: date, key findings, action items. Notify Quality agent of any security/quality findings for inclusion in KNOWN_FAILURES.md." | 🟡 | Grok feedback currently goes nowhere |

**Lines added: ~30 | Total after: ~117**

---

### AGENT 7: 🚂 Conductor
**File:** `~/.openclaw/workspace-conductor/AGENTS.md`

| # | Change | Priority | Evidence |
|---|--------|----------|----------|
| D1 | **Add mandatory local Docker verification to Pre-Deploy Checklist:** "BEFORE `git push origin main`, run: (1) `docker build -t project .` (2) `docker run -d --env-file .env.example -p 8000:8000 project` (3) `curl -f http://localhost:8000/health` — must return 200 (4) Check runtime logs: `docker logs <container>` — no crash loops (5) `docker stop && docker rm`. If ANY step fails, DO NOT push. Fix and retry." | 🔴 | Mar 16: No local verification = Railway is the first test environment |
| D2 | **Add credential pre-verification:** "Before deploying apps that connect to external services (Google APIs, Anthropic, OpenAI, etc.), verify the credentials work: (a) Check env vars are set in Railway Variables tab (b) If possible, test the API key locally: `curl -H 'Authorization: Bearer $KEY' https://api.example.com/health`. Report any missing or invalid credentials BEFORE triggering deploy." | 🔴 | Mar 13: Auth failures cascaded because nobody checked first |
| D3 | **Add explicit Preflight Check Protocol** (replaces vague "check infra" reference in pipeline): "Conductor Preflight runs BEFORE Coder starts and verifies: (a) Docker Desktop installed and running (b) Railway project exists and is linked to GitHub repo (c) Required Railway services are provisioned (PostgreSQL, Redis, MinIO) (d) All required env vars are set in Railway Variables tab (e) GitHub Actions CI workflow exists and is passing. Write results to `PREFLIGHT.md` in project directory." | 🟡 | Pipeline mentions "Conductor preflight" but it was never documented |
| D4 | **Add rollback procedure:** "If deployment fails after push: (1) `git revert HEAD` + `git push` to restore last working state (2) Check Railway auto-redeploy triggers on the revert (3) Verify health check passes on reverted version (4) Report to Jarvis: what failed, which commit broke it, revert commit hash." | 🟡 | Currently just "check SKILL.md Section X" — no actionable steps |
| D5 | **Add Windows PC as build environment option.** New section: `## 🖥️ Remote Build on Windows PC`. When Jarvis indicates the project requires heavy Docker builds or GPU: (a) SSH to `ericbrown@100.67.128.123` via Tailscale (b) Verify Docker + NVIDIA runtime: `docker --version && nvidia-smi` (c) Run `docker build` on the Windows PC (faster builds, more RAM) (d) Run Docker container tests on Windows PC (e) Push to GitHub from Windows PC → Railway auto-deploys (f) Verify Railway deployment from Mac side: `curl -f https://APP.up.railway.app/health`. **Pre-check:** Always run `tailscale ping remote-coder-main` before attempting SSH. If Windows PC is offline, fall back to MacBook builds and notify Eric. **Note:** Railway runs Linux containers — verify that Docker images built on Windows (which uses WSL2/Linux) deploy correctly to Railway. | 🔴 | New: Heavy Docker builds can run on 128GB/GPU machine instead of MacBook |

**Lines added: ~65 | Total after: ~178**

---

### CROSS-CUTTING: KNOWN_FAILURES.md Updates

| # | New Entry | Priority |
|---|-----------|----------|
| KF1 | **Railway: railway.json startCommand conflicts with Dockerfile CMD** — Use Dockerfile CMD only. Remove startCommand from railway.json. Use `sh -c` form for variable expansion. | 🔴 |
| KF2 | **Railway: pgvector CREATE EXTENSION must precede create_all** — Separate transactions. Run extension creation first, commit, then create_all. | 🟡 |
| KF3 | **Railway: Celery broker not ready at startup** — Set `broker_connection_retry_on_startup=True`. Railway services start in parallel. | 🟡 |
| KF4 | **Railway: PORT variable expansion fails in exec form** — Use `CMD ["/bin/sh", "-c", "uvicorn ... --port ${PORT:-8000}"]` not `CMD ["uvicorn", "--port", "$PORT"]`. | 🟡 |
| KF5 | **Auth cascade: Multiple credentials expire simultaneously** — Pre-check auth health before credential-dependent work. Fallback: Zapier MCP for email, Telegram for notifications. | 🟡 |
| KF6 | **Cron storm: Same job runs multiple times** — Check `memory/cron-state.json` for last successful run before re-executing. | 🟡 |

---

### CROSS-CUTTING: TOOLS.md Updates

| # | Change | Priority |
|---|--------|----------|
| T1 | **Add Windows Remote Coder section** to TOOLS.md with full machine specs, SSH access details, available tools, and GPU capabilities. | 🔴 |

**New TOOLS.md section:**
```markdown
## Windows Remote Coder PC (remote-coder-main)
- **Tailscale IP:** 100.67.128.123
- **Hostname:** remote-coder-main
- **OS:** Windows 11 25H2
- **CPU:** 32 vCPUs
- **RAM:** 128 GB
- **GPU:** NVIDIA RTX 5080 Blackwell (CUDA 13.1)
- **SSH:** ericbrown@100.67.128.123 (port 22, OpenSSH Server)
- **Docker:** Docker Desktop with NVIDIA Container Toolkit (GPU passthrough)
- **Git:** Configured with Eric's GitHub credentials
- **Use for:** Heavy Docker builds, GPU/CUDA workloads, large codebases (>50K lines), ML model training/inference
- **NOT for:** Light web apps, simple API servers, quick fixes (use MacBook)
- **Pre-check:** `tailscale ping remote-coder-main` before every SSH session
- **Key expiry:** Disabled (permanent Tailscale access)
- **Remote Coder Agent:** FastAPI on port 8443 (HTTPS) for browser-based desktop access
```

---

## GROK'S ADDITIONAL RECOMMENDATIONS (Accepted)

| # | Recommendation | Action |
|---|---------------|--------|
| GR1 | **Agent testing/simulation** — Simulate incidents (auth failures, DB ordering, Docker failures) to validate agent responses without hitting production | Noted for future — would require a test harness |
| GR2 | **Version control for agent configs** — Track AGENTS.md changes in git to detect regressions | Already happening via workspace git commits |
| GR3 | **Inter-agent JSON schemas for handoffs** — Standardize HANDOFF.md format validation | Good idea, defer to v2 |

## GROK'S REJECTED SUGGESTIONS

| Suggestion | Why Rejected |
|-----------|-------------|
| Merge Auditor into Quality | Auditor serves a distinct purpose (external review gate + Grok packaging). Merging would overload Quality. |
| Event-driven pub/sub architecture | Over-engineering for a single-user system. Current sequential pipeline works. |
| Secondary orchestrator for Jarvis failover | Unnecessary complexity — Jarvis failures are rare and self-heal infrastructure already handles gateway restarts. |

---

## SUMMARY: CHANGE COUNT

| Agent | 🔴 Critical | 🟡 Important | Total Changes |
|-------|------------|-------------|---------------|
| Jarvis | 4 | 3 | 7 |
| Researcher | 0 | 4 | 4 |
| Planner | 3 | 2 | 5 |
| Coder | 4 | 4 | 8 |
| Quality | 2 | 3 | 5 |
| Auditor | 1 | 2 | 3 |
| Conductor | 3 | 2 | 5 |
| KNOWN_FAILURES | 1 | 5 | 6 |
| TOOLS.md | 1 | 0 | 1 |
| **TOTAL** | **19** | **25** | **44** |

---

## NEXT STEPS (Pending Eric's Approval)

1. Eric reviews this proposal
2. Eric approves all, approves with modifications, or rejects specific items
3. Jarvis implements approved changes to all agent AGENTS.md files
4. Jarvis updates KNOWN_FAILURES.md with new entries
5. Jarvis updates TOOLS.md with Windows PC details
6. Jarvis commits all changes with descriptive commit message
7. Quality Agent runs a verification audit on the updated configs
8. Verify SSH connectivity to Windows PC (pending OpenSSH Server installation)

---

*Analysis: Jarvis (Opus 4.6) | Cross-Review: Grok 4 | Recursive self-improvement cycle #1*
