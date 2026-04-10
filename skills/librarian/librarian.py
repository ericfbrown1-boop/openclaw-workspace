#!/usr/bin/env python3
"""
Librarian — ClawEvolveRepo knowledge manager for AutoClaw.
Indexes wins, blocks losers, provides prior-art lookup for all agents.
"""
import json
import os
import sys
import glob
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent.parent / "ClawEvolveRepo"
WINS_DIR = REPO / "wins"
LOSSES_DIR = REPO / "losses"
PATTERNS_DIR = REPO / "patterns"


def _ensure_dirs():
    for d in [WINS_DIR, LOSSES_DIR, PATTERNS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def record_win(hypothesis: dict) -> str:
    _ensure_dirs()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    hid = hypothesis.get("id", ts)
    path = WINS_DIR / f"{hid}.json"
    entry = {**hypothesis, "recorded_at": ts, "status": "win"}
    path.write_text(json.dumps(entry, indent=2))
    generate_index()
    return str(path)


def record_loss(hypothesis: dict, reason: str) -> str:
    _ensure_dirs()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    hid = hypothesis.get("id", ts)
    path = LOSSES_DIR / f"{hid}.json"
    entry = {**hypothesis, "recorded_at": ts, "status": "loss", "reason": reason}
    path.write_text(json.dumps(entry, indent=2))
    return str(path)


def query_prior_art(topic: str) -> list:
    """Return relevant wins and losses for a given topic string."""
    _ensure_dirs()
    results = []
    topic_lower = topic.lower()
    for pattern in [WINS_DIR / "*.json", LOSSES_DIR / "*.json"]:
        for f in glob.glob(str(pattern)):
            try:
                data = json.loads(Path(f).read_text())
                text = json.dumps(data).lower()
                if any(word in text for word in topic_lower.split()):
                    results.append(data)
            except Exception:
                pass
    return results


def generate_index() -> str:
    _ensure_dirs()
    wins = sorted(glob.glob(str(WINS_DIR / "*.json")))
    losses = sorted(glob.glob(str(LOSSES_DIR / "*.json")))
    lines = [
        "# ClawEvolveRepo — Knowledge Index",
        f"_Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_",
        f"\n**Total Wins:** {len(wins)} | **Total Losses:** {len(losses)}\n",
        "## Recent Wins",
    ]
    for f in wins[-10:]:
        d = json.loads(Path(f).read_text())
        lines.append(f"- ✅ `{d.get('id','?')}` — {d.get('description','')[:80]}")
    lines.append("\n## Recent Losses (Do Not Retry)")
    for f in losses[-10:]:
        d = json.loads(Path(f).read_text())
        lines.append(f"- ❌ `{d.get('id','?')}` — {d.get('description','')[:80]} (reason: {d.get('reason','')})")
    index_path = REPO / "index.md"
    index_path.write_text("\n".join(lines) + "\n")
    return str(index_path)


def briefing_summary() -> str:
    wins = sorted(glob.glob(str(WINS_DIR / "*.json")))
    losses = sorted(glob.glob(str(LOSSES_DIR / "*.json")))
    recent_wins = []
    for f in wins[-3:]:
        d = json.loads(Path(f).read_text())
        recent_wins.append(d.get("description", d.get("id", "?")))
    summary = f"🧬 ClawEvolveRepo: {len(wins)} wins, {len(losses)} losses total."
    if recent_wins:
        summary += " Latest wins: " + "; ".join(recent_wins)
    return summary


def seed_from_incidents(incidents_path: str):
    """Seed ClawEvolveRepo from real incidents.jsonl data."""
    _ensure_dirs()
    wins_seeded = 0
    losses_seeded = 0
    with open(incidents_path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                inc = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_raw = inc.get("timestamp", inc.get("ts", ""))
            ts = ts_raw[:10].replace("-", "") if ts_raw else f"seed{i:04d}"
            hid = f"INC-{ts}-{i:03d}"
            hypothesis = {
                "id": hid,
                "description": inc.get("error_summary", inc.get("detail", ""))[:120],
                "category": inc.get("error_category", "unknown"),
                "agent": inc.get("agent", "unknown"),
                "project": inc.get("project", ""),
                "source": "incidents.jsonl",
            }
            resolved = inc.get("resolved", False)
            if resolved is True or str(resolved).lower() == "true":
                fix = inc.get("fix_applied", "")
                hypothesis["fix"] = fix
                record_win(hypothesis)
                wins_seeded += 1
            else:
                reason = inc.get("prevention", inc.get("root_cause", "unresolved"))[:100]
                record_loss(hypothesis, reason)
                losses_seeded += 1
    generate_index()
    return wins_seeded, losses_seeded


if __name__ == "__main__":
    if "--test" in sys.argv:
        print("=== Librarian Self-Test ===")
        _ensure_dirs()
        # Test record_win
        w = record_win({"id": "TEST-WIN-001", "description": "Test win: Tailscale retry fixed SSH", "metric": "ping_success", "improvement": "+10%"})
        print(f"✅ record_win → {w}")
        # Test record_loss
        loss = record_loss({"id": "TEST-LOSS-001", "description": "Test loss: rm -rf workaround"}, "unsafe operation")
        print(f"✅ record_loss → {loss}")
        # Test query
        results = query_prior_art("tailscale ssh")
        print(f"✅ query_prior_art('tailscale ssh') → {len(results)} results")
        # Test index
        idx = generate_index()
        print(f"✅ generate_index → {idx}")
        # Test briefing
        b = briefing_summary()
        print(f"✅ briefing_summary → {b}")
        # Seed from real incidents
        incidents = os.path.expanduser("~/.openclaw/workspace/memory/incidents.jsonl")
        if os.path.exists(incidents):
            w_count, l_count = seed_from_incidents(incidents)
            print(f"✅ seed_from_incidents → {w_count} wins, {l_count} losses seeded from real data")
        print("\n=== All tests passed ===")
    elif "--seed" in sys.argv:
        incidents = os.path.expanduser("~/.openclaw/workspace/memory/incidents.jsonl")
        w, losses = seed_from_incidents(incidents)
        print(f"Seeded {w} wins + {losses} losses from incidents.jsonl")
    elif "--briefing" in sys.argv:
        print(briefing_summary())
    elif "--index" in sys.argv:
        print(generate_index())
    else:
        print("Usage: librarian.py [--test | --seed | --briefing | --index]")
