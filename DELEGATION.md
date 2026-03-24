# DELEGATION.md — Agent Routing Rules

## → Planner Agent (agentId: planner)
Trigger: "plan", "design", "architect", "new project", "build a", "start a", "create a system"
Action: spawn planner with project description. Planner commissions Researcher automatically.
Never go straight to Coder for non-trivial new projects.

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

**A) Error Diagnosis:** Trigger: "error", "failed", "crash", "bug". Quality diagnoses → sends fix to Coder. Never send errors directly to Coder.

**J5 — Error Classification:** Before dispatch, classify as: import | auth | Docker | Railway | database | other.

**B) Security Audit:** Trigger: new code committed, before making repo public, after Coder completes, on demand.

## → Coder Agent (agentId: coder)
Trigger: explicit coding task where a plan already exists. Must read PLAN.md first.

**Verify Your Work (Anthropic #1 Rule):** After EVERY code change, run the project's test suite. If no tests exist, write at least one smoke test (health endpoint check, lint pass, basic unit test) before creating HANDOFF.md. Never hand off untested code.

**Git-Before-HANDOFF:** `git add . && git commit && git push` before creating HANDOFF.md. Record commit SHA. If no repo exists → `git init` + `gh repo create` first.

**Read Before Write:** Before writing any new code, read at least 3 existing files in the project to understand patterns, conventions, and style. Reference existing patterns in your implementation. Don't invent new conventions when the project already has them.

**Hybrid Build Routing:** >15min builds route to PowerSpec. Record host in HANDOFF.md.

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

**Anthropic Code Review Check:** On every audit, verify that Anthropic's Code Review feature (launched Mar 2026 — multi-agent PR review) is enabled on all active GitHub repos. If not enabled, flag it and recommend setup. This supplements our Quality Part B security audit with Anthropic's own PR review agents.

**Weekly Claude Best Practices Audit (standing instruction):**
Every Monday, the External Auditor must:
1. Fetch the latest Claude/Claude Code best practices from Anthropic's official docs:
   - https://docs.anthropic.com/en/docs/claude-code/overview
   - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
   - https://docs.anthropic.com/en/docs/build-with-claude/agentic-tool-use
   - https://docs.anthropic.com/en/docs/claude-code/best-practices
   - Search for any new Anthropic blog posts or changelog entries from the past 7 days
2. Compare findings against ALL current agent configuration files:
   - `AGENTS.md`, `DELEGATION.md`, `PIPELINE.md`, `POWERSPEC.md`, `INCIDENTS.md`
   - `skills/monitor/SKILL.md`, `skills/remote-coder/SKILL.md`
   - Any per-agent workspace AGENTS.md files under `~/.openclaw/agents/*/agent/`
3. Produce a report at `plans/claude-best-practices-audit.md` with:
   - New/changed Anthropic recommendations found
   - Current agent files that conflict with or miss these recommendations
   - Specific suggested changes (with before/after diffs where helpful)
   - Priority ranking (critical alignment gaps vs nice-to-haves)
4. Send the report to Eric via Telegram for review + approval
5. Do NOT apply changes until Eric approves — this is a review gate, not auto-update
6. After Eric approves, implement changes, commit to GitHub, and update the lessons table in Monitor SKILL.md

## → Conductor Agent — Completion Gate
**The 100% Rule:** No task is complete unless committed to GitHub.

**Status mapping:** queued=0% | running=1-99% (milestones only, NEVER time-based) | completed=100% (after git push) | failed=blocked

**Progress milestones:** Code written=25% | Tests pass=50% | Quality review=75% | Git push=100%

**Conductor must update tasks.json** with: `completedCommit`, `completedAt`, `deliverablePath`, `deliverableEmailTs`.

**Deliverable Scan Gate:** Code tasks need git push + SHA. Report tasks need email + Gmail ID. Both need proof in tasks.json.

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
Trigger: AFTER External Auditor completes; post-deployment review.

**Incident-Driven Learning:** Weekly scan `memory/incidents.jsonl` for patterns (>2 same category). Propose AGENTS.md/SKILL.md updates. Track in `memory/skill-suggestions.md`.
