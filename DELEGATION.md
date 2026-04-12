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

**Learn First (Librarian Feedback Loop — Standing Change 2026-03-30, auto-injected by orchestrator 2026-04-11):**

When a plan is produced via `~/openclaw-workspace/scripts/jarvis_pipeline.py`, the orchestrator automatically reads every `.md` file under `~/.claude/projects/*/memory/` (excluding `MEMORY.md` index files) and injects them into the Planner's prompt as `=== LIBRARIAN MEMORY — PAST LESSONS ===` **before** the TASK section. Planner MUST:

1. Read the entire memory section before drafting
2. Reflect every applicable lesson as an explicit constraint, checkpoint, or verification step in PLAN.md
3. Cite the memory filename next to each checkpoint that was informed by a past lesson
4. Include a `## Past Lessons Applied` section at the end of PLAN.md listing every memory file consulted and how it shaped the plan (or "not applicable" if it does not apply)
5. If a feedback memory says "don't do X" or "always do Y", the plan MUST reflect that — Auditor will reject plans that silently ignore memory files

**When dispatched outside the orchestrator** (manual `openclaw agent --agent planner` invocation), Planner should still read the memory files directly from disk, but note that the agent sandbox (`fs.workspaceOnly: true`) may block this — prefer the orchestrator path.

**This creates a recursive learning loop:** Agents do work → Librarian captures learnings → Memory files updated → Orchestrator auto-injects them into the next Planner/Auditor/Coder dispatch → Better execution → Librarian captures new learnings → cycle continues. Fully closed at Planner (proactive), Auditor (adversarial), and Coder (implementation) stages as of 2026-04-11.

**Explore First (Anthropic Best Practice):** Before creating PLAN.md, Planner MUST:
1. Read the existing codebase structure (`find . -type f | head -50`, key config files)
2. Understand current patterns, frameworks, and conventions already in use
3. Only then create the plan — never plan in a vacuum

**Hybrid Capacity Plan:** Every PLAN.md must include a "Compute Allocation" table assigning each task to MacBook or PowerSpec. Default is PowerSpec. See `POWERSPEC.md`.

**Git & Repo Mandate:** Every PLAN.md must include a "Repository Setup" section. No coding begins until the repo exists on GitHub.

**PowerSpec Pre-Check:** Before finalizing any plan with >15min tasks, run `tailscale ping remote-coder-main`.

### 📊 Diagram-First Planning (Standing Change 2026-04-12 — MANDATORY)

**Every PLAN.md MUST begin with visual architecture diagrams BEFORE any prose, task decomposition, or ADRs.** This is non-negotiable.

**Minimum required diagrams (all in Mermaid syntax):**
1. **System Architecture** — `graph TD` or `C4Context` showing all components and connections
2. **Process/Data Flow** — `flowchart` or `sequenceDiagram` showing the primary workflow

**Additional diagrams (required when applicable):**
- `erDiagram` — for any project with a database or data model
- `graph` deployment topology — for multi-service / Docker / Railway projects
- `stateDiagram-v2` — for workflows with complex state transitions
- `sequenceDiagram` — for multi-service API interactions

**Diagram standards:**
- Label ALL arrows (what data/action flows between components)
- Show failure paths, not just the happy path
- Include all external systems (APIs, DBs, third-party services)
- Use node styling for visual clarity

**Gate:** A PLAN.md without the minimum 2 diagrams is INVALID and must not proceed to Phase 3 (Implement). The Grok 4.20 Beta adversarial review MUST check diagram completeness.

**Origin:** Eric directive 2026-04-12 — "Make this diagram-based approach a mandatory part of your Planning Agent and planning phase for ALL projects."


## → Researcher Agent (agentId: researcher)
Trigger: research requests NOT related to a new project plan (financial analysis, market news, competitive intelligence).
Action: spawn researcher with a specific brief and source filters.

**Research Artifact Rule:** All outputs must be committed to Git before handoff. Offload >15min research to PowerSpec via SSH.

## → Quality Agent (agentId: quality)
**Model (Standing Change 2026-04-11):** Quality runs on **Grok 4.20 Beta** (`xai/grok-4.20`), same provider plumbing as the External Auditor. Rationale: Quality's job is adversarial output-correctness judgment — exactly what Grok 4.20 Beta proved excellent at in the 2026-04-11 powerspec-rebuild pipeline test (6 concrete gaps, all applied). Fallback chain: `xai/grok-4.20 → anthropic/claude-opus-4-6 → anthropic/claude-sonnet-4-6`. Fixes the 2026-03-27 INCIDENTS.md lesson "checked status, not content".

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

**Learn Before Code (Librarian Feedback Loop — Standing Change 2026-03-30, auto-injected by orchestrator 2026-04-11):**

When Coder is dispatched via `~/openclaw-workspace/scripts/jarvis_pipeline.py`, the orchestrator automatically reads every `.md` file under `~/.claude/projects/*/memory/` (excluding `MEMORY.md` index files) and injects them into the Coder's prompt as `=== LIBRARIAN MEMORY — PAST LESSONS ===` **before** the merged PLAN.md. Coder MUST:

1. Read the entire memory section before writing code
2. Apply each relevant lesson as a code-level constraint (e.g., if memory says "launchd plists using /usr/bin/env need EnvironmentVariables.PATH", every plist Coder writes must include it)
3. If a PLAN.md instruction conflicts with a past lesson, **follow the past lesson** and flag the conflict in the final summary — the plan may be wrong and Auditor missed it
4. Return a `## Past Lessons Applied` section in the final summary listing every memory file consulted and how it shaped the implementation

**When dispatched outside the orchestrator** (manual `openclaw agent --agent coder`, Claude Code `--print` invocation, or direct shell), Coder should still read memory files directly but is not guaranteed filesystem access. Prefer the orchestrator path for production pipelines.

**This creates a recursive loop:** Past coding failures are captured by Librarian → stored in memory files → orchestrator auto-injects them on next task → prevents recurrence. Each deployment teaches the system. Planner gets the same injection (see "Learn First" rule above) so the loop is closed at both ends: proactive (plan avoids the bug) and enforcement (if the plan misses it, Coder catches the conflict; if Coder misses it, Auditor catches the gap).

**Read Before Write:** Before writing any new code, read at least 3 existing files in the project to understand patterns, conventions, and style. Reference existing patterns in your implementation. Don't invent new conventions when the project already has them.

**Hybrid Build Routing:** >15min builds route to PowerSpec. Record host in HANDOFF.md.

### 🎛️ Option C — PowerSpec dispatch via openclaw nodes (Standing Change 2026-04-11)

Coder can now run on PowerSpec directly via `jarvis_pipeline.py`'s `task.execution.coderHost` field:

```json
"execution": {
  "coderHost": "powerspec",
  "remoteWorkDir": "C:\\Users\\Eric Brown\\repos\\<task-id>",
  "remoteGitRepo": "https://github.com/ericfbrown1-boop/<repo>.git"
}
```

Default is `"local"` (Mac). When `"powerspec"`, the orchestrator:

1. **Plumbing (SSH)**: ensures the remote work dir exists, stages `_prompt.txt` with the full Coder brief + Librarian memory, reads back `_output.txt` + git sha
2. **Workload (openclaw nodes)**: dispatches via `openclaw agent --agent main` with the `exec` tool routing to `host=PowerSpec`. Main instructs the PowerSpec node host to run `cmd /c type _prompt.txt | claude.cmd --print --dangerously-skip-permissions --model sonnet > _output.txt`
3. **Mission Control**: every coder-stage agentChain entry gets `host: "powerspec"` so the dashboard reflects which machine did the work

The Coder on PowerSpec HAS ACCESS to Librarian memory (injected via the prompt file) and will honor past lessons — verified 2026-04-11 smoke test where PowerSpec Claude Code ran `/simplify` quality audit before committing, matching the `feedback_quality_audit.md` rule.

**Prerequisites (one-time)**:
- PowerSpec openclaw paired with Mac gateway (`openclaw nodes approve <requestId>`)
- PowerSpec node.json gateway set to Mac Tailscale IP (100.101.203.113:18789)
- PowerSpec `exec-approvals.json` has `defaults.security=full, ask=off, askFallback=full` (or allowlist entries)
- OpenClaw Node scheduled task on PowerSpec running
- Mac: `openclaw approvals allowlist add --agent "*" --node PowerSpec "**\\claude.cmd"` (+ git.exe, node.exe, cmd.exe)

See `powerspec_openclaw_nodes_setup.md` memory for the idempotent reproduction script.

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
Trigger: AFTER Quality security audit passes. FINAL step in code pipeline. Also spawnable on-demand by Jarvis for system audits, config reviews, and skill health checks.

**Spawn allowlist:** auditor is now included in main agent allowAgents (updated 2026-04-10). Can be spawned via sessions_spawn with agentId: auditor.

**Pipeline:** Coder → Quality → External Auditor → Done

### 🧠 Learn Before Review Rule (Standing Change 2026-04-11)

**Every adversarial review MUST apply past lessons from the Librarian memory files.**

The orchestrator (`scripts/jarvis_pipeline.py` → `stage_auditor`) automatically loads every `.md` file under `~/.claude/projects/*/memory/` (excluding `MEMORY.md` index files) and injects them into the Auditor's prompt before the PLAN.md to be reviewed. Auditor MUST:

1. Read the entire `=== LIBRARIAN MEMORY — PAST LESSONS ===` section before evaluating the plan.
2. For every lesson that applies to the plan being reviewed, either:
   - **Verify** the plan already handles it (note in `### Applied Lessons` section as "confirmed"), OR
   - **Add a HIGH-severity gap** in `### Gaps` citing the specific memory filename, e.g. `[HIGH] (jarvis_launchd_path_bug.md) — plist missing EnvironmentVariables.PATH`
3. Every gap that originates from a past lesson must reference the memory filename so Jarvis can trace the learning chain.
4. Unaddressed lessons are **never** acceptable; they indicate the Planner skipped the "Learn First" step or didn't read the relevant file. Flag the plan for revision.

**Why this matters:** Without this rule, each session re-discovers the same bugs. With it, the system gets measurably smarter over time — every fix writes a memory file, and every subsequent review enforces that fix as a constraint. This closes the recursive learning loop described in AGENTS.md.

**Orchestrator auto-injection:** Auditor runs in a sandboxed workspace (`fs.workspaceOnly: true`) and cannot read memory files directly. The orchestrator reads them on Auditor's behalf and passes them inline in the prompt. Memory size is capped at 250KB (Grok 4.20 Beta has 2M context so this is generous). If the cap is hit, the prompt includes a truncation notice.

### Best-in-Class QA Gate (6 steps)
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

**Port Conflict Check (Standing Change 2026-03-30):**
Before ANY `pm2 start` or `pm2 restart` on PowerSpec, run:
```bash
docker ps --format "{{.Names}} {{.Ports}}" | grep -E "300[0-1]"
```
If a Docker container occupies port 3000 or 3001, stop it first. PowerSpec runs many Docker services simultaneously — port collisions cause silent failures where pm2 reports "online" but traffic goes to Docker instead.
**Origin:** FinancialReportApp Docker container on :3001 intercepted Mission Control backend traffic, causing dashboard to render wrong content.

**Mission Control Health Probe:**
After starting Mission Control, verify with: `curl -s http://localhost:3001/health | grep MissionControl`
The backend health endpoint returns `{"app": "MissionControl"}` — if this doesn't match, a port conflict exists.

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
2. **Weekly scheduled Librarian sweep** (`com.openclaw.librarian.weekly.plist`, Sundays 06:00) runs `scripts/librarian_weekly.py` which scans `memory/incidents.jsonl` for recurring patterns (≥2 incidents in same category within 7 days) and writes a `type: feedback` report to `~/.claude/projects/-Users-ericbrown-powerspec-rebuild/memory/librarian_weekly_patterns.md`. This file is then auto-injected into Planner/Auditor/Coder on the next pipeline run via `load_librarian_memory()`.
3. Planner, Auditor, and Coder automatically receive ALL memory files via orchestrator injection (see "Learn First", "Learn Before Review", and "Learn Before Code" rules) — no manual reads required when dispatched via `jarvis_pipeline.py`
4. The orchestrator also supports auto-revision on rejection: Auditor REJECT → Planner re-drafts with feedback (up to `--max-revision-loops N`, default 2); Quality LLM REJECT → Coder re-implements with feedback. Deterministic verificationCmd failure does NOT retry — it halts.
5. This means every bug fixed, every deployment pattern discovered, every user preference recorded automatically improves all future work
6. Librarian should prefer updating existing memory files over creating new ones to avoid bloat

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
