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

## Model Tiering Strategy

| Agent | Model | Rationale |
|-------|-------|-----------|
| Jarvis (main) | Opus 4.6 | Orchestration needs best reasoning |
| Planner | Opus 4.6 | Architecture needs depth |
| Coder | Sonnet 4.6 | Code tasks well-defined; saves ~40-60% |
| Tester | Sonnet 4.6 | Test execution is deterministic |
| Quality | Sonnet 4.6 | Checklist-driven |
| Conductor | Sonnet 4.6 | Infrastructure tasks well-defined |
| External Auditor | Sonnet 4.6 | Packaging is straightforward |
| Librarian | Sonnet 4.6 | Analysis can use cheaper model |
| Monitor | Sonnet 4.6 | Simple monitoring tasks |
| Researcher | Sonnet 4.6 | Web search + synthesis |
