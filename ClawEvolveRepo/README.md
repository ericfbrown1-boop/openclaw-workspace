# ClawEvolveRepo

The growing knowledge repository for AutoClaw — Jarvis's self-improving coding system.

Inspired by Karpathy's autoresearch (github.com/karpathy/autoresearch).

## Structure
- `wins/`     — Validated improvements that were merged
- `losses/`   — Rejected hypotheses (never retry these)
- `patterns/` — Extracted cross-cutting patterns from wins
- `index.md`  — Auto-generated summary of all wins/losses

## How It Works
1. AutoClaw detects recurring failures in incidents.jsonl
2. Proposes a concrete fix (hypothesis)
3. Tests in dry-run mode, then live
4. Records outcome here — wins merge to main, losses are blocked forever
5. All agents query this repo before starting work

Maintained by: AutoClaw + Librarian
Last seeded: April 7, 2026
