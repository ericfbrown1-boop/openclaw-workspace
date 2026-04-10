---
name: librarian
description: >
  ClawEvolveRepo knowledge manager. Indexes AutoClaw wins/losses, provides prior-art
  lookup for all agents, generates daily briefing summaries of improvements.
---

# Librarian — Knowledge Manager for AutoClaw

## What It Does
- Records wins (merged fixes) and losses (rejected hypotheses) in ClawEvolveRepo
- Provides prior-art lookup so agents never repeat failed ideas
- Generates daily briefing section: "AutoClaw overnight wins"
- Auto-generates index.md with full history

## Use It
```bash
# All agents should query before starting work:
python3 ~/.openclaw/workspace/skills/librarian/librarian.py --index

# Seed from incidents (run once or after major incidents):
python3 ~/.openclaw/workspace/skills/librarian/librarian.py --seed

# Get briefing summary:
python3 ~/.openclaw/workspace/skills/librarian/librarian.py --briefing
```

## ClawEvolveRepo Location
~/.openclaw/workspace/ClawEvolveRepo/
- wins/     — JSON files for each successful improvement
- losses/   — JSON files for each rejected hypothesis (blocked)
- patterns/ — Cross-cutting patterns from wins
- index.md  — Human-readable full history
