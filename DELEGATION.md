# DELEGATION.md — Agent Routing Rules
> **L1:** Which agent handles which task. 9 agents with trigger keywords, handoff gates, and completion rules. Includes Conductor dual-write and global dispatch template.

## → Planner Agent (agentId: planner)
Trigger: "plan", "design", "architect", "new project", "build a", "start a", "create a system"
Action: spawn planner with project description. Planner commissions Researcher automatically.
Never go straight to Coder for non-trivial new projects.

### 🧠 Dual-Model Planning Process (Standing Change 2026-03-27)

**Every plan is built in 3 stages using two LLMs for maximum quality:**

**Stage 1: Research (Researcher Agent)**
Before ANY planning begins, Researcher gathers latest information:
- Search reputable sources for the specific task domain (official docs, best practices, known pitfalls)
- Identify key success factors, common failure modes, and production requirements
- Produce a Research Brief with findings, citing sources
- This research DIRECTLY informs the plan — no planning in a vacuum

**Stage 2: Draft Plan (Opus 4.6)**
Planner (Opus 4.6) creates PLAN.md informed by the Research Brief:
- Architecture, task decomposition, risk mitigation
- Key success factors from research embedded as explicit checkpoints
- Verification criteria for every task (how to prove it works)
- Compute allocation, git setup, Docker/deployment requirements

**Stage 3: Adversarial Review (Grok 4.20 Beta)**
Spawn Grok 4.20 Beta (`xai/grok-4`) to review the draft plan:
- Identify gaps, missing edge cases, architectural weaknesses
- Challenge assumptions with "what if X fails?" scenarios
- Propose additions to verification criteria
- Focus on production-readiness and failure prevention
Jarvis merges Grok's feedback into the final PLAN.md before dispatching to Coder.

**The output: a plan informed by fresh research, drafted by Opus, stress-tested by Grok.**

**Claude Code Auto Mode Assumption:** All plans should assume Coder runs Claude Code with `--permission-mode auto`. This means:
- File reads, writes, and test execution happen without prompts (low-risk classifier)
- Plans do NOT need manual approval checkpoints between each file change
- Plans SHOULD include verification steps (run tests, check output) since auto mode enables fast iteration
- High-risk operations (bulk deletes, env changes) will still prompt — plans should note these explicitly

**Output Parity Checkpoint:** Every PLAN.md for apps with multiple output channels must include a "Delivery Parity" section specifying: (1) which channels exist, (2) how the single source file is served to each, (3) hash verification strategy.

**Learn First (Librarian Feedback Loop — Standing Change 2026-03-30):**
Before ANY planning begins, Planner MUST read Librarian memory files to absorb past learnings:
1. Read `~/.claude/projects/C--Users-ericf/memory/MEMORY.md` — index of all captured learnings
2. Read ALL `feedback_*.md` files referenced in MEMORY.md — these contain rules from past mistakes and validated approaches
3. Read ALL `project_*.md` files relevant to the domain being planned — these contain deployment details, architecture decisions, and context
4. Read ALL `reference_*.md` files that may inform the plan — external system pointers, API patterns
5. Incorporate relevant learnings directly into PLAN.md as explicit constraints or checkpoints
6. If a feedback memory says "don't do X" or "always do Y", the plan MUST reflect that

**This creates a recursive learning loop:** Agents do work → Librarian captures learnings → Memory files updated → Next plan reads those learnings → Better execution → Librarian captures new learnings → cycle continues.

**Explore First (Anthropic Best Practice):** Before creating PLAN.md, Planner MUST:
1. Read the existing codebase structure (`find . -type f | head -50`, key config files)
2. Understand current patterns, frameworks, and conventions already in use
3. Only then create the plan — never plan in a vacuum

**Hybrid Capacity Plan:** Every PLAN.md must include a "Compute Allocation" table assigning each task to MacBook or PowerSpec. Default is PowerSpec. See `POWERSPEC.md`.

**Git & Repo Mandate:** Every PLAN.md must include a "Repository Setup" section. No coding begins until the repo exists on GitHub.

**PowerSpec Pre-Check:** Before finalizing any plan with >15min tasks, run `tailscale ping remote-coder-main`.

## → Researcher Agent (agentId: researcher)
Trigger: research requests NOT related to a new project plan (financial analysis, market news, competitive intelligence).
Action: spawn researcher with a specific brief and source filters.

**Research Artifact Rule:** All outputs must be committed to Git before handoff. Offload >15min research to PowerSpec via SSH.

## → Quality Agent (agentId: quality)
**Two workflows — Error Diagnosis AND Security Audit:**

**Q-Status Alignment Rule:** After any coding change touching dashboards/status/progress, Quality must verify ALL user-facing views match `/api/backend/tasks`. Mismatches = block release + log incident.

**Deliverable Verification Rule:** For report tasks, verify: final doc exists, email was sent (Gmail message ID), `deliverablePath` + `deliverableEmailTs` populated in `tasks.json`.

**UI Link Audit Rule:** Click every nav link and interactive element during QA. Dead links = auto-fail.

**Correctness-First Rule:** Quality Agent's primary job is verifying OUTPUT CORRECTNESS, not just code correctness. A pipeline with no errors that produces empty output has FAILED Quality review.

**A) Error Diagnosis:** Trigger: "error", "failed", "crash", "bug". Quality diagnoses → sends fix to Coder. Never send errors directly to Coder.

**Root Cause Research Rule (MANDATORY):** Before proposing ANY fix, Quality must:
1. Search the exact error message on official docs + Stack Overflow + GitHub issues
2. Check if this is a known issue with a permanent solution (not just a workaround)
3. If the problem has occurred before (check `memory/incidents.jsonl`), research WHY the previous fix didn't stick
4. Include research sources in the diagnosis: "Found via [source]: the root cause is X, permanent fix is Y"
5. **Never propose a workaround when a root cause fix exists.**

**J5 — Error Classification:** Before dispatch, classify as: import | auth | Docker | Railway | database | other.

**B) Security Audit:** Trigger: new code committed, before making repo public, after Coder completes, on demand.

## → Coder Agent (agentId: coder)
Trigger: explicit coding task where a plan already exists. Must read PLAN.md first.

**Correctness-First Rule:** Every code change must be provably correct. "It runs without errors" is necessary but NOT sufficient. The OUTPUT must be verified — run the pipeline and check what the user would actually receive.

**Claude Code: Auto Mode (Standing Change 2026-03-28)**
When spawning Claude Code for coding tasks, ALWAYS use `--permission-mode auto`:
```bash
cd /path/to/project && claude --permission-mode auto --print 'Your task'
```
- Auto mode uses a safety classifier to allow low-risk actions (file reads, tests, linting) automatically
- High-risk actions (deleting files, running unknown scripts) still prompt
- This replaces `--permission-mode bypassPermissions` which skipped ALL checks
- Do NOT use `--dangerously-skip-permissions` — auto mode is the correct balance of speed and safety
- **Origin:** Eric directive 2026-03-28

**Verify Your Work (Anthropic #1 Rule):** After EVERY code change, run the project's test suite. If no tests exist, write at least one smoke test (health endpoint check, lint pass, basic unit test) before creating HANDOFF.md. Never hand off untested code.

**Output Parity Rule:** When code delivers output through multiple channels (email + download, API + UI, etc.), ALL channels must serve the exact same content. Generate once, hash it, serve from one source, verify integrity on every delivery. See PIPELINE.md "Output Parity Rule" for implementation pattern.

**Git-Before-HANDOFF:** `git add . && git commit && git push` before creating HANDOFF.md. Record commit SHA. If no repo exists → `git init` + `gh repo create` first.

**Learn Before Code (Librarian Feedback Loop — Standing Change 2026-03-30):**
Before writing ANY code, Coder MUST read Librarian memory files for applicable learnings:
1. Read `~/.claude/projects/C--Users-ericf/memory/MEMORY.md` — index of all captured learnings
2. Read ALL `feedback_*.md` files — these are hard-won rules from past bugs, deployment failures, and validated approaches
3. Read `project_*.md` files for the current project — deployment details, architecture decisions, service configurations
4. Read `reference_*.md` files relevant to the tech stack — API patterns, external system pointers
5. Apply feedback learnings as code constraints (e.g., if memory says "add boto3 timeouts" → do it in every S3 client)
6. If a learning conflicts with PLAN.md, raise it — the learning may indicate the plan missed something

**This creates a recursive loop:** Past coding failures are captured by Librarian → stored in feedback memories → read by Coder on next task → prevents recurrence. Each deployment teaches the system.

**Read Before Write:** Before writing any new code, read at least 3 existing files in the project to understand patterns, conventions, and style. Reference existing patterns in your implementation. Don't invent new conventions when the project already has them.

**Hybrid Build Routing:** >15min builds route to PowerSpec. Record host in HANDOFF.md.

**Version Check Rule (Standing Change 2026-03-29):**
Before using ANY library API, check the installed version:
- `cat node_modules/<pkg>/package.json | grep version` (Node.js)
- `pip show <pkg>` (Python)
Compare with the examples/docs you're referencing. Breaking changes between major versions cause silent failures.
**Origin:** Ceregent session — pg-boss v10, Stripe SDK, Next.js 15 all had breaking API changes from their docs/examples.

**Next.js Monorepo Standalone Rules (Standing Change 2026-03-29):**
When deploying Next.js from a monorepo with `output: "standalone"`:
1. MUST set `outputFileTracingRoot: path.join(__dirname, "../../")` (path to monorepo root)
2. MUST add `extensionAlias: { ".js": [".ts", ".tsx", ".js"] }` if workspace packages use ESM .js extensions
3. MUST wrap `useSearchParams()` in `<Suspense>` (Next.js 15+ requirement)
4. Database connections MUST be lazy (Proxy pattern) — module-level `new Pool()` crashes during build/SSG
5. Never hardcode PORT in Dockerfile — let the platform assign it
**Origin:** Ceregent deploy — 5 separate failures all traced to monorepo standalone misconfiguration.

**Secret Safety Rule (Standing Change 2026-03-29):**
- NEVER use string fallbacks for secrets: `process.env.SECRET || "default"` is a production vulnerability
- Instead: throw in production, only fallback in development with NODE_ENV check
- ALL secret comparisons (API keys, webhook signatures, service tokens) must use `crypto.timingSafeEqual()`
- After ANY variable rename/refactor, grep for the old name to catch missed references
**Origin:** Ceregent Quality Agent caught 3 security issues in one audit.

**J3 — Deployment Readiness Gate (4 checks):**
- (a) `docker build .` succeeds
- (b) `docker run` + `curl localhost:PORT/health` returns 200
- (c) HANDOFF.md exists
- (d) `git push` succeeded (SHA in HANDOFF.md)

## → Tester Agent (agentId: tester)
Trigger: AFTER Coder completes; BEFORE Quality audit.

**Minimum Test Gate:** Every project MUST have at least a basic test suite (health endpoint check, lint pass, one unit test) before it can proceed to Quality. If no tests exist, Tester creates them.

**Deliverable Check:** Verify output doc exists + email queued/sent for report tasks.
**Hybrid Test Distribution:** >15min test suites split across MacBook + PowerSpec.

## → External Auditor Agent (agentId: auditor)
Trigger: AFTER Quality security audit passes. FINAL step in code pipeline.

**Pipeline:** Coder → Quality → External Auditor → Done

**Best-in-Class QA Gate (6 steps):**
1. Pull + Build (verify tree matches GitHub)
2. Smoke Test as User (every nav item, no placeholders/dead links)
   - Git commit verification + hardware utilization check + deliverable block
3. Dashboard Integrity (Task Board = Agents = Mission Control)
4. Deliverable Verification (doc exists, email sent, paths logged)
5. Regression Checklist (lint, tests)
6. Sign-off Artifact (update tasks.json with completedCommit, completedAt, deliverablePath)

Only after all 6 pass can a task reach 100%.

See `skills/auditor/SKILL.md` for standing instructions (Code Review check, daily vibe coding scan, weekly Claude best practices audit).

## → Conductor Agent (agentId: conductor) — Completion Gate
**The 100% Rule:** No task is complete unless committed to GitHub.

**Status mapping:** queued=0% | running=1-99% (milestones only, NEVER time-based) | completed=100% (after git push) | failed=blocked

**Progress milestones:** Code written=25% | Tests pass=50% | Quality review=75% | Git push=100%

**DUAL WRITE (MANDATORY):** On EVERY task update, Conductor writes to BOTH:
1. `~/.openclaw/workspace/tasks.json` — OpenClaw source of truth
2. `~/JarvisMissionControl/backend/data/tasks.json` — Dashboard display

Fields to update: `completedCommit`, `completedAt`, `deliverablePath`, `deliverableEmailTs`, `status`, `progress`.

**If Mission Control tasks.json uses array format**, find the task by `id` and update in place. If the task doesn't exist in the array, append it as a new entry with all required fields (`id`, `title`, `status`, `owner`, `priority`, `summary`, `progress`, `agentChain`, `updates`).

**Deliverable Scan Gate:** Code tasks need git push + SHA. Report tasks need email + Gmail ID. Both need proof in BOTH tasks.json files.

**Auto-Wake PowerSpec:** If any queued task has >15min remaining and PowerSpec is offline → 3 wake retries → alert Eric.

**Hybrid Execution:** Load-balance across MacBook + PowerSpec. Record hosts in HANDOFF.md.

## 📋 Global Dispatch Rule (Anthropic Best Practice)
When dispatching work to ANY agent, Jarvis must always include:
- **(a) Specific file paths** — not "update the config" but "update `/JarvisMissionControl/Dockerfile`"
- **(b) Example patterns to follow** — "use the pattern in `docker-compose.yml`" or "match the style in `GlassCard.tsx`"
- **(c) Explicit success criteria** the agent can verify programmatically — "build succeeds", "curl /health returns 200", "tests pass"
Vague dispatches waste context and produce wrong results.

## → Monitor Agent (agentId: monitor)
Trigger: "check stocks", "MicroCenter", "system health", or automated cron.
See `skills/monitor/SKILL.md` for the full 11-step sweep checklist.

**Core guarantees:**
1. Auth never expires (auto-reauth gog, verify gh every sweep)
2. Nothing stalls (>2h no progress = investigate + act)
3. PowerSpec always working (idle GPU + queued tasks = alert)
4. Every failure triggers RCA (see `INCIDENTS.md`)

## → Librarian Agent (agentId: librarian)
Trigger: AFTER External Auditor completes; post-deployment review; after any Railway/Docker deployment; on user request ("run Librarian").

**Incident-Driven Learning:** Weekly scan `memory/incidents.jsonl` for patterns (>2 same category). Propose AGENTS.md/SKILL.md updates. Track in `memory/skill-suggestions.md`.

**Memory File Output (Standing Change 2026-03-30):**
Librarian writes learnings to `~/.claude/projects/C--Users-ericf/memory/` using these types:
- `feedback_*.md` — Rules from mistakes and validated approaches (highest priority for Planner + Coder)
- `project_*.md` — Deployment details, architecture decisions, service configurations
- `reference_*.md` — External system pointers, API patterns, tool usage guides
- `user_*.md` — User preferences and role context
Each file uses YAML frontmatter (name, description, type) and MEMORY.md is the index.

**Recursive Loop Contract:**
1. After every deployment or significant coding session, Librarian captures learnings as memory files
2. Planner reads ALL memory files before creating PLAN.md (see "Learn First" rule)
3. Coder reads ALL memory files before writing code (see "Learn Before Code" rule)
4. This means every bug fixed, every deployment pattern discovered, every user preference recorded automatically improves all future work
5. Librarian should prefer updating existing memory files over creating new ones to avoid bloat

## Subagent Timeout Policy (Standing Change 2026-03-27)

**Match timeout to task complexity. Never use a short timeout for complex work.**

| Complexity | Timeout | Examples |
|-----------|---------|----------|
| SIMPLE | 120s (2 min) | Single file edit, quick fix |
| MODERATE | 600s (10 min) | Multi-file change, one concern |
| COMPLEX | 1800s (30 min) | Full-stack app, multi-service build |
| HEAVY | 3600s (60 min) | Large codebase refactor, full project build |

**Rule:** For any task with >10 files to create, use minimum 1800s timeout.
**Origin:** First Coder agent for FinancialReportApp timed out at 600s after building 14/40 files. Eric directive: "That should definitely not happen."

## 🔴 Silent Failure Prevention Rules (Standing Change 2026-03-27)
**Origin:** FinancialReportApp RCA — reports appeared "done" with zero content because failures were silently swallowed.

### Applies to ALL Agents:

**1. Output Quality Validation (MANDATORY)**
Every agent that produces a deliverable (report, email, analysis, dashboard update) must validate the OUTPUT CONTENT, not just the pipeline status.
- "Status: done" ≠ "Content: verified"
- Check that the deliverable contains meaningful data, not just defaults/placeholders
- Example: a .docx report must have >100 chars in its executive summary and must NOT contain >3 instances of "not available"

**2. No Silent Fallbacks**
When any component falls back to a default value (empty string, placeholder text, error dict), it MUST:
- Log a WARNING with the field name and reason
- If >3 fields fall back in a single pipeline run, FAIL the pipeline (don't produce a garbage deliverable)
- Never mark a task "done" when its content is placeholder text

**3. Environment Validation on Container Startup**
Any Docker-deployed app must validate required env vars on startup:
- Check key format (e.g., API keys must match expected prefix + minimum length)
- Check key connectivity (e.g., test API call returns 200)
- Fail FAST on startup, not silently during execution

**4. Separate Parsers for Separate Schemas**
Never share a JSON parser between components that expect different output shapes (e.g., tagger vs synthesis). Each schema gets its own parser with its own fallback that matches the expected shape. Alternatively, use structured output features (Anthropic `output_format`, OpenAI JSON mode) to guarantee schema compliance.

**5. Integration Test Before Deploy**
Before declaring any Docker app "working," run an E2E test that:
- Submits a real request through the full pipeline
- Waits for completion
- Opens/reads the output artifact
- Asserts the output contains real content (not defaults)
This is the ONLY valid proof that the app works. Status codes and log messages are necessary but NOT sufficient.
