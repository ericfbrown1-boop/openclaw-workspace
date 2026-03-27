# PIPELINE.md — Code Pipeline, Completion Gates & Dashboard Rules
> **L1:** 4-phase workflow (Understand→Plan→Implement→Verify), task complexity gate, model tiering with costs, API budget gate, dual-write dashboard rule, test oracle references, E2E verification checklist.

## 4-Phase Workflow (MANDATORY for ALL task types)

Every task — code, research, audit, monitoring — follows these 4 phases:

```
Phase 1: UNDERSTAND → Phase 2: PLAN → Phase 3: IMPLEMENT → Phase 4: VERIFY
```

| Phase | What Happens | Who | Gate to Next Phase |
|-------|-------------|-----|-------------------|
| **1. UNDERSTAND** | Read codebase, gather requirements, identify constraints. "Explore First" rule. | Planner + Researcher | PROJECT_CONTEXT.md exists |
| **2. PLAN** | Design approach, decompose tasks, identify risks, set verification criteria. | Planner (+ GPT-5.4 cross-review) | PLAN.md approved by Jarvis |
| **3. IMPLEMENT** | Execute the plan. Write code, send reports, run analysis. Verify at each CHECKPOINT. | Coder / Researcher / Conductor | HANDOFF.md + git push |
| **4. VERIFY** | Test, review, audit, deploy. Multi-gate: Tester → Quality → Auditor → Conductor. | Tester + Quality + Auditor + Conductor | Completion gate passes (SHA or email ID in tasks.json) |

**Apply to ALL task types:**
- **Code tasks:** Understand codebase → Plan architecture → Implement code → Verify (tests + deploy)
- **Research tasks:** Understand question → Plan search strategy → Implement research → Verify findings (cross-check sources)
- **Error diagnosis:** Understand error context → Plan investigation → Implement fix → Verify fix works
- **Monitoring tasks:** Understand alert condition → Plan check → Implement sweep → Verify system healthy
- **Report tasks:** Understand requirements → Plan outline → Implement writing → Verify deliverable sent

## Complete Code Pipeline (Detailed)

```
Phase 1: UNDERSTAND
  → Planner reads existing codebase ("Explore First" rule)
  → Researcher gathers requirements if needed
  → Output: PROJECT_CONTEXT.md

Phase 2: PLAN
  → Planner creates PLAN.md (architecture, tasks, risks, compute allocation)
  → GPT-5.4 cross-review for edge cases
  → Jarvis merges review + confirms environment ready
  → Output: Final PLAN.md

Phase 3: IMPLEMENT
  → Coder implements (writes CHECKPOINT.md at each phase)
  → Coder verifies at each checkpoint (tests, Docker build, health check)
  → Output: HANDOFF.md + git push

Phase 4: VERIFY
  → Tester (import verification + test suite)
    → If FAIL: returns to Coder (Phase 3)
    → If PASS: HANDOFF.md for Quality
  → Quality (Security Audit + Code Review)
    → If CRITICAL: BFG cleanup, loop back to Phase 3
    → If CLEAN: proceed
  → External Auditor (6-step QA gate)
  → Conductor (Docker build + deploy + smoke tests)
  → Librarian (post-audit review, suggests improvements)
  → Code shipped ✅
```

## Global Completion Gate

No task may reach 100% / `completed` without BOTH:
1. **Code tasks:** `git push` succeeded + commit SHA in `tasks.json`
2. **Report tasks:** deliverable emailed + Gmail message ID in `tasks.json`

Enforced by Conductor, verified by External Auditor, monitored by Monitor.

## Task Complexity Gate (Anthropic: "only use multi-agent for high-value parallelizable tasks")

Before spawning ANY subagent, classify the task:

| Complexity | Time Est | Scope | Action |
|-----------|----------|-------|--------|
| **SIMPLE** | < 5 min | Single file edit, quick fix | Jarvis does it directly. NO subagent. |
| **MODERATE** | 5-30 min | Multi-file, one concern | Single subagent with verification command |
| **COMPLEX** | > 30 min | Multi-step, parallelizable | Up to 3 concurrent subagents, each with plan |

**Ask before spawning:** "Could I do this in 2 minutes myself?" If yes → do it. Don't waste tokens on agent overhead.

**Token budget awareness:** Multi-agent uses ~15x more tokens than chat (per Anthropic). Only COMPLEX tasks justify the cost.

## Context Management Rules (Anthropic Best Practice)

**Cron payload limit:** No cron job message payload should exceed 500 tokens. Instead of embedding full instructions, have agents read their SKILL.md file for details. The cron message should be a brief trigger with a pointer to the skill.

**Isolated sessions:** Each pipeline stage runs in an isolated session (enforced by OpenClaw agent spawning). The main session orchestrates but does NOT execute heavy work. This prevents context bloat.

**Context hygiene:** When compaction warnings appear or context gets heavy, proactively save state to memory files and start fresh rather than dragging a massive conversation forward. Files survive sessions; context doesn't.

**Verification criteria:** Every task dispatch must include success criteria that the agent can verify programmatically (e.g., "tests pass", "curl /health returns 200", "lint clean"). Tasks without verification criteria are incomplete.

## Dashboard-as-Source-of-Truth Rule (DUAL WRITE)

**Two tasks.json files must stay in sync:**
1. `~/.openclaw/workspace/tasks.json` — OpenClaw agents read/write (source of truth)
2. `~/JarvisMissionControl/backend/data/tasks.json` — Mission Control dashboard reads

**Every agent** must update **BOTH** `tasks.json` files when:
- Task starts → `status: "running"` + `progress: 25`
- Milestone hit → increment `progress` (25 → 50 → 75)
- Task completes → `status: "completed"` + `progress: 100` (only after gate passes)
- Task fails/cancelled → `status: "failed"` + `error` field
- New task created → add immediately with `status: "queued"`

**New projects** appear on Task Board the moment they are requested.
**Monitor** verifies every 5 minutes; stale entries (>2h no update) trigger alert.
**Eric should never have to ask "status?"**

## API Budget Cost Gate (MANDATORY)

Before any Opus 4.6 task, check `memory/api-usage-state.json`:

| Budget Used | Action |
|-------------|--------|
| < 75% | Normal operations — use Model Tiering below |
| 75–90% | **Downgrade**: All non-critical tasks use Sonnet 4.6 (only Jarvis orchestration stays on Opus) |
| > 90% | **Pause**: Non-essential work stops. Alert Eric. Only critical fixes proceed (on Sonnet) |

Agents read `alert_level` from the state file:
- `"none"` or `"info"` → normal
- `"warning"` → downgrade to Sonnet
- `"critical"` → pause + alert

## Model Tiering Strategy

| Agent | Model | Context | Cost (in/out per M) | Rationale |
|-------|-------|---------|---------------------|-----------|
| Jarvis (main) | Opus 4.6 | 200K | $15 / $75 | Orchestration needs best reasoning |
| Planner | Opus 4.6 | 200K | $15 / $75 | Architecture needs depth |
| Planner (cross-review) | GPT-5.4 Pro | 1M | $2.50 / $15 | 1M context for full codebase analysis; 33% fewer hallucinations; speed perspective |
| Coder | Sonnet 4.6 | 200K | $3 / $15 | Code tasks well-defined; saves ~40-60% |
| Tester | Sonnet 4.6 | 200K | $3 / $15 | Test execution is deterministic |
| Quality | Sonnet 4.6 | 200K | $3 / $15 | Checklist-driven |
| Conductor | Sonnet 4.6 | 200K | $3 / $15 | Infrastructure tasks well-defined |
| External Auditor | Sonnet 4.6 | 200K | $3 / $15 | Packaging is straightforward |
| Librarian | Sonnet 4.6 | 200K | $3 / $15 | Analysis can use cheaper model |
| Monitor | Sonnet 4.6 | 200K | $3 / $15 | Simple monitoring tasks |
| Researcher | Sonnet 4.6 | 200K | $3 / $15 | Web search + synthesis |

### Model Fallback Chain
If a primary model is unavailable (rate limit, outage, cooldown):
1. **Opus 4.6** → GPT-5.4 Pro → Sonnet 4.6
2. **GPT-5.4 Pro** → Opus 4.6 → Sonnet 4.6
3. **Sonnet 4.6** → Grok 4 Fast → Haiku 4.5

## Test Oracle Schemas

Every task type has a formal verification schema in `skills/auditor/TEST_ORACLES.md`. Agents MUST:
1. **Planner**: Include the relevant oracle in PLAN.md `successCriteria`
2. **Coder/Researcher**: Self-check against oracle BEFORE writing HANDOFF.md
3. **Tester**: Validate oracle checks programmatically
4. **Monitor**: Verify completed tasks satisfy their oracle (Step 11: 4-Phase Compliance)

Available oracles: `task_completion`, `code_task`, `research_task`, `report_task`, `error_diagnosis`, `monitoring_sweep`, `earnings_analysis`, `competitive_intel`.

## E2E Verification Checklist

Before marking any pipeline run complete, verify:
1. **Agent health:** Each agent responds to a test prompt
2. **Delegation:** Keyword triggers route to correct agent (test each trigger)
3. **Pipeline flow:** Task flows Planner → Coder → Tester → Quality → Auditor → Conductor without stalling
4. **Completion gate:** tasks.json shows commit SHA and/or email ID
5. **Cron jobs:** All scheduled jobs show `lastStatus: "ok"` in `memory/cron-state.json`
6. **Fallbacks:** Simulate auth failure → verify fallback path activates

## Pre-Commit Quality Gate (MANDATORY)

**No code may be committed without passing ALL of these checks first.** This is a standing process change (2026-03-27).

### Checklist (run in order):

```
1. SYNTAX CHECK    node --check <file>  (for every new/modified .js/.ts file)
2. TEST SUITE      npm test  (or equivalent — must pass, zero failures)
3. LINT            eslint / ruff / shellcheck if configured (warnings OK, errors block)
4. SECRET SCAN     grep -r "sk-ant\|sk-proj\|ghp_\|API_KEY=" <new files>  (must be clean)
5. DRY RUN         Execute the primary code path once (e.g. --help, --dry-run, or a single-page test)
6. DIFF REVIEW     git diff --staged  — read what you're committing, verify no debug code or temp files
```

### Enforcement:

| Check | Blocks Commit? | Who Runs It |
|-------|---------------|-------------|
| Syntax check | ✅ Yes | Coder / Jarvis |
| Test suite | ✅ Yes | Coder / Quality |
| Lint | ⚠️ Errors only | Coder |
| Secret scan | ✅ Yes | Quality / pre-commit hook |
| Dry run | ✅ Yes | Coder |
| Diff review | ✅ Yes | Jarvis (before `git commit`) |

### Quick Command:

```bash
# Run all checks in one shot (Node.js projects)
for f in $(git diff --cached --name-only --diff-filter=ACM | grep '\.js$'); do node --check "$f" || exit 1; done \
  && npm test \
  && ! grep -r 'sk-ant\|sk-proj\|ghp_\|API_KEY=' $(git diff --cached --name-only) \
  && echo "✅ Quality gate passed — safe to commit"
```

**Origin:** Eric directive 2026-03-27 — "Make sure you apply Quality Agent before committing code"
