# Planner Agent GPT-5.4 Upgrade Plan

**Source:** references/GPT54_Enhanced_Planning_Agent.docx
**Status:** Ready for implementation

## Why Upgrade

| Metric | Current (Opus 4.6) | GPT-5.4 Pro |
|--------|-------------------|-------------|
| Context window | 200K tokens | 1M tokens (5x) |
| Input cost | $15 / M tokens | $2.50 / M tokens (6x cheaper) |
| Output cost | $75 / M tokens | $15 / M tokens (5x cheaper) |
| Hallucination rate | Baseline | ~33% fewer (per OpenAI benchmarks) |
| Best for | Reasoning, orchestration | Large codebase analysis, planning |

**Key benefit:** 1M context window means the Planner can ingest an entire codebase before creating PLAN.md, reducing the "Planner Missing Edge Cases" failure pattern (currently ~15% of plans per KNOWN_FAILURES.md).

## Architecture

GPT-5.4 is used as a **cross-review model**, not a replacement for Opus:
1. Planner (Opus 4.6) creates initial PLAN.md
2. GPT-5.4 Pro reviews the plan with full codebase context (1M window)
3. Planner incorporates feedback and finalizes

This is already referenced in DELEGATION.md ("GPT 5.4 cross-review").

## Implementation Steps

### Step 1: Add OpenAI API Key
```bash
# On Mac — add to openclaw.json or environment
export OPENAI_API_KEY="sk-..."
```
Store in 1Password Jarvis vault, inject via `op` CLI.

### Step 2: Configure Model in openclaw.json
Add GPT-5.4 to the Planner agent's model fallback chain:
```json
{
  "id": "planner",
  "model": {
    "primary": "claude-opus-4-6",
    "fallbacks": ["gpt-5.4-pro", "claude-sonnet-4-6"]
  }
}
```

### Step 3: Update Planner System Prompt
Add to Planner's AGENTS.md or agent config:
- "Use GPT-5.4 Pro for cross-review when codebase exceeds 100K tokens"
- "Plan-first: decide architecture before writing any code"
- "Cumulative diff sandbox: changes stay separate until approved"

### Step 4: Validate
```bash
# Test planner responds
openclaw agent test planner "Create a plan for a simple REST API"

# Test cross-review
openclaw agent test planner "Review this plan for edge cases: [paste plan]"

# Verify model selection
openclaw agent info planner
```

## Cost Impact
- Planner currently uses ~5-10% of total API budget (most usage is Coder/Monitor)
- Switching Planner cross-review to GPT-5.4: saves ~$10-20/month on planning tasks
- Net effect: better plans (fewer Coder rework loops) + lower cost

## Risks
- OpenAI API availability (mitigated by fallback chain)
- Different response format from Opus (mitigated by structured output prompts)
- API key management (mitigated by 1Password integration)

## References
- references/GPT54_Enhanced_Planning_Agent.docx (full upgrade guide with bash scripts)
- PIPELINE.md Model Tiering Strategy (updated with GPT-5.4 row)
- AUTH_FALLBACKS.md Model Fallback Chain (updated)
