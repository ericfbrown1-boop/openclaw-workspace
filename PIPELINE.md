# PIPELINE.md — Code Pipeline, Completion Gates & Dashboard Rules

## Complete Code Pipeline

```
Eric request → Planner (if new project)
  → Jarvis merges review + confirms environment ready
  → Final PLAN.md + PROJECT_CONTEXT.md
  → Coder (implementation)
    → Writes CHECKPOINT.md at each phase
    → Writes HANDOFF.md on completion
  → Tester (import verification + test suite)
    → If FAIL: returns to Coder
    → If PASS: HANDOFF.md for Quality
  → Quality (Security Audit + Code Review)
    → If CRITICAL: BFG cleanup, loop back
    → If CLEAN: proceed
  → External Auditor (6-step QA gate + optional Grok review)
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

## Dashboard-as-Source-of-Truth Rule

Mission Control (`tasks.json`) must reflect real-time state of ALL projects at ALL times.

**Every agent** must update `tasks.json` when:
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

## E2E Verification Checklist

Before marking any pipeline run complete, verify:
1. **Agent health:** Each agent responds to a test prompt
2. **Delegation:** Keyword triggers route to correct agent (test each trigger)
3. **Pipeline flow:** Task flows Planner → Coder → Tester → Quality → Auditor → Conductor without stalling
4. **Completion gate:** tasks.json shows commit SHA and/or email ID
5. **Cron jobs:** All scheduled jobs show `lastStatus: "ok"` in `memory/cron-state.json`
6. **Fallbacks:** Simulate auth failure → verify fallback path activates
