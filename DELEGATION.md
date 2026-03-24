# DELEGATION.md — Agent Routing Rules

## → Planner Agent (agentId: planner)
Trigger: "plan", "design", "architect", "new project", "build a", "start a", "create a system"
Action: spawn planner with project description. Planner commissions Researcher automatically.
Never go straight to Coder for non-trivial new projects.

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

**Git-Before-HANDOFF:** `git add . && git commit && git push` before creating HANDOFF.md. Record commit SHA. If no repo exists → `git init` + `gh repo create` first.

**Hybrid Build Routing:** >15min builds route to PowerSpec. Record host in HANDOFF.md.

**J3 — Deployment Readiness Gate (4 checks):**
- (a) `docker build .` succeeds
- (b) `docker run` + `curl localhost:PORT/health` returns 200
- (c) HANDOFF.md exists
- (d) `git push` succeeded (SHA in HANDOFF.md)

## → Tester Agent (agentId: tester)
Trigger: AFTER Coder completes; BEFORE Quality audit.

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

## → Conductor Agent — Completion Gate
**The 100% Rule:** No task is complete unless committed to GitHub.

**Status mapping:** queued=0% | running=1-99% (milestones only, NEVER time-based) | completed=100% (after git push) | failed=blocked

**Progress milestones:** Code written=25% | Tests pass=50% | Quality review=75% | Git push=100%

**Conductor must update tasks.json** with: `completedCommit`, `completedAt`, `deliverablePath`, `deliverableEmailTs`.

**Deliverable Scan Gate:** Code tasks need git push + SHA. Report tasks need email + Gmail ID. Both need proof in tasks.json.

**Auto-Wake PowerSpec:** If any queued task has >15min remaining and PowerSpec is offline → 3 wake retries → alert Eric.

**Hybrid Execution:** Load-balance across MacBook + PowerSpec. Record hosts in HANDOFF.md.

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
