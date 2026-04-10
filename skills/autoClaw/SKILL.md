---
name: autoclaw
description: >
  AutoClaw self-evolving coding loop. Detects recurring failures from incidents.jsonl,
  proposes code fixes, simulates outcomes, commits winners, blocks losers in ClawEvolveRepo.
  Run via Monitor Step 13 every 4 hours or on-demand.
---

# AutoClaw — Self-Evolving Coding System

Inspired by Karpathy's autoresearch. One script, one loop, continuous improvement.

## Run It
```bash
# Dry run (safe — no real changes):
AUTOCLAW_DRY_RUN=true python3 ~/.openclaw/workspace/skills/autoclaw/autoclaw.py

# Live mode (applies fixes):
AUTOCLAW_DRY_RUN=false python3 ~/.openclaw/workspace/skills/autoclaw/autoclaw.py
```

## Safety Rules
- Protected files: SOUL.md, USER.md, MEMORY.md, AUTH_FALLBACKS.md, .env — NEVER touched
- Max 3 hypotheses per cycle
- Max 50 lines changed per hypothesis
- All changes tested before merge
- DRY_RUN=true by default — set false to enable live fixes

## Output
- Results: memory/autoclaw-test-results-YYYYMMDD.md
- ClawEvolveRepo: wins/ and losses/ updated every cycle
- Librarian index regenerated automatically
