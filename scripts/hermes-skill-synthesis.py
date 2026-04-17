#!/usr/bin/env python3
"""
Hermes Supervisor — Skill Synthesis Engine (Phase 4)
Self-contained: runs analyze + auto-create in one pass. No CLI args needed.
Stdout is injected as context for the Hermes supervisor cron LLM.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = Path.home() / ".openclaw/workspace/ClawEvolveRepo"
SKILLS_DIR = Path.home() / ".openclaw/workspace/skills"
LOG_FILE = Path.home() / ".openclaw/workspace/memory/hermes-supervisor.log"
SYNTHESIS_STATE = Path.home() / ".openclaw/workspace/memory/hermes-synthesis-state.json"
AUTO_CREATE_THRESHOLD = 0.75


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5_000_000:
        LOG_FILE.rename(LOG_FILE.with_suffix(".log.1"))
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts()}] {msg}\n")


def load_entries() -> tuple[list, list]:
    wins, losses = [], []
    for subdir, target in [(REPO_DIR / "wins", wins), (REPO_DIR / "losses", losses)]:
        if subdir.exists():
            for f in subdir.glob("*.json"):
                try:
                    d = json.loads(f.read_text())
                    d["_file"] = str(f)
                    target.append(d)
                except Exception:
                    pass
    return wins, losses


KEYWORD_MAP = {
    "gateway": ["gateway", "startup", "restart"],
    "auth": ["auth", "oauth", "token", "credential"],
    "email": ["email", "gmail", "delivery"],
    "report": ["report", "docx", "financial"],
    "docker": ["docker", "container", "deploy"],
    "ssh": ["ssh", "tailscale", "remote"],
    "memory": ["memory", "context", "session"],
    "cron": ["cron", "schedule", "heartbeat"],
    "quality": ["quality", "gate", "validation", "empty"],
}


def extract_tags(entry: dict) -> list[str]:
    tags = list(entry.get("tags", []))
    category = entry.get("category", "")
    if category:
        tags.append(category)
    title = entry.get("title", "").lower()
    for tag, keywords in KEYWORD_MAP.items():
        if any(kw in title for kw in keywords):
            tags.append(tag)
    return list(set(tags))


def skill_exists(tag: str) -> bool:
    """Check for both exact tag name AND auto-prefixed name."""
    return (SKILLS_DIR / tag).exists() or (SKILLS_DIR / f"auto-{tag}-patterns").exists()


def analyze(wins: list, losses: list) -> list[dict]:
    tag_wins: dict[str, list] = defaultdict(list)
    tag_losses: dict[str, list] = defaultdict(list)

    for w in wins:
        for t in extract_tags(w):
            tag_wins[t].append(w)
    for loss in losses:
        for t in extract_tags(loss):
            tag_losses[t].append(l)

    suggestions = []
    for tag in set(tag_wins) | set(tag_losses):
        w, n_losses = len(tag_wins[tag]), len(tag_losses[tag])
        total = w + n_losses
        if total < 2:
            continue
        confidence = w / total
        recurrence = min(total / 5.0, 1.0)
        if confidence < 0.5 and l < 2:
            continue
        priority = round(confidence * 0.6 + recurrence * 0.4, 2)
        suggestions.append({
            "tag": tag,
            "wins": w,
            "losses": l,
            "total": total,
            "confidence": round(confidence, 2),
            "priority": priority,
            "already_exists": skill_exists(tag),
            "sample_wins": [e.get("title", "")[:80] for e in tag_wins[tag][:3]],
            "sample_losses": [e.get("title", "")[:80] for e in tag_losses[tag][:3]],
        })

    return sorted(suggestions, key=lambda x: x["priority"], reverse=True)


def create_skill(suggestion: dict, wins: list, losses: list) -> bool:
    tag = suggestion["tag"]
    skill_name = f"auto-{tag}-patterns"
    skill_dir = SKILLS_DIR / skill_name

    if skill_dir.exists():
        return False

    skill_dir.mkdir(parents=True, exist_ok=True)

    relevant_wins = [w for w in wins if tag in extract_tags(w)][:10]
    relevant_losses = [loss for loss in losses if tag in extract_tags(loss)][:5]

    fixes = []
    for w in relevant_wins:
        fix = w.get("fix") or w.get("resolution") or w.get("summary", "")
        if fix and len(fix) > 20:
            fixes.append(f"- {fix[:200]}")
    fix_text = "\n".join(fixes[:8]) if fixes else "- See ClawEvolveRepo wins/ for details"

    win_text = "\n".join(
        f"- {w.get('title', 'Unknown')} (ID: {w.get('id', '?')})"
        for w in relevant_wins
    ) or "- See ClawEvolveRepo wins/ for details"

    loss_text = "\n".join(
        f"- {loss.get('title', 'Unknown')} — Reason: {loss.get('reason', loss.get('resolution', 'unresolved'))}"
        for loss in relevant_losses
    ) or "- None recorded yet"

    content = f"""---
name: {skill_name}
description: >
  Auto-synthesized from {suggestion['total']} ClawEvolveRepo entries on tag '{tag}'.
  Confidence: {suggestion['confidence']:.0%}, Priority: {suggestion['priority']:.2f}.
  Generated by Hermes Supervisor Phase 4 on {datetime.now().strftime('%Y-%m-%d')}.
---

# {skill_name.replace('-', ' ').title()}

**Auto-generated** | Source: ClawEvolveRepo tag `{tag}` | {suggestion['wins']}W / {suggestion['losses']}L | Priority {suggestion['priority']:.2f}

## Proven Fixes

{fix_text}

## Known Working Patterns

{win_text}

## Known Failures — Do NOT Retry

{loss_text}

## Search ClawEvolveRepo

```bash
jq 'select(.tags[]? == "{tag}")' ~/.openclaw/workspace/ClawEvolveRepo/wins/*.json
```

_Generated: {ts()} | Re-run synthesis to update: `python3 ~/.openclaw/workspace/scripts/hermes-skill-synthesis.py`_
"""
    (skill_dir / "SKILL.md").write_text(content)
    log(f"[SKILL_SYNTHESIS] Created: {skill_name} ({suggestion['wins']}W/{suggestion['losses']}L)")
    return True


def load_state() -> dict:
    if SYNTHESIS_STATE.exists():
        try:
            return json.loads(SYNTHESIS_STATE.read_text())
        except Exception:
            pass
    return {"last_run": None, "skills_created": 0, "total_runs": 0}


def save_state(state: dict):
    SYNTHESIS_STATE.write_text(json.dumps(state, indent=2))


def main():
    wins, losses = load_entries()
    suggestions = analyze(wins, losses)
    state = load_state()
    state["total_runs"] = state.get("total_runs", 0) + 1
    state["last_run"] = ts()

    eligible = [s for s in suggestions if s["priority"] >= AUTO_CREATE_THRESHOLD and not s["already_exists"]]
    created = []
    for s in eligible:
        if create_skill(s, wins, losses):
            created.append(s["tag"])

    state["skills_created"] = state.get("skills_created", 0) + len(created)
    save_state(state)

    # Output for LLM context
    print(f"[SKILL_SYNTHESIS] Analyzed {len(wins)} wins, {len(losses)} losses → {len(suggestions)} patterns")
    print(f"[SKILL_SYNTHESIS] Created {len(created)} new skills: {created if created else 'none'}")
    print()
    print(f"{'Tag':<25} {'W':>4} {'L':>4} {'Priority':>9} {'Exists':>7}")
    print("-" * 55)
    for s in suggestions[:10]:
        exists_str = "✓" if s["already_exists"] else "NEW" if s["priority"] >= AUTO_CREATE_THRESHOLD else "—"
        print(f"{s['tag']:<25} {s['wins']:>4} {s['losses']:>4} {s['priority']:>9.2f} {exists_str:>7}")

    if created:
        print(f"\nNew skills created this run: {', '.join(created)}")

    log(f"[SKILL_SYNTHESIS] Run complete: {len(created)} created from {len(eligible)} eligible")


if __name__ == "__main__":
    main()
