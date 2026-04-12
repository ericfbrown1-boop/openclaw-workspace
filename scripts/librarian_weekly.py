#!/usr/bin/env python3
"""librarian_weekly.py — Weekly pattern scanner for the Librarian feedback loop.

Runs every Sunday at 06:00 via `com.openclaw.librarian.weekly.plist`. Scans
`~/openclaw-workspace/memory/incidents.jsonl` for patterns over the last 7 days,
groups by `error_category`, and writes a pattern report to the Librarian memory
directory so future pipeline runs (via `jarvis_pipeline.py`) automatically pick
up the lessons through `load_librarian_memory()`.

This is intentionally deterministic — no LLM dispatch. The scanner surfaces
factual patterns; Jarvis (in main conversation) can synthesize them into
higher-level feedback_*.md rules when appropriate.

Output: `~/.claude/projects/-Users-ericbrown-powerspec-rebuild/memory/librarian_weekly_patterns.md`
        (frontmatter type=feedback so load_librarian_memory picks it up)

No external deps — stdlib only, runs under any launchd PATH.
"""
from __future__ import annotations

import collections
import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
INCIDENTS_PATH = HOME / "openclaw-workspace" / "memory" / "incidents.jsonl"
REPORT_DIR = HOME / ".claude" / "projects" / "-Users-ericbrown-powerspec-rebuild" / "memory"
REPORT_PATH = REPORT_DIR / "librarian_weekly_patterns.md"
LOG_DIR = HOME / "openclaw-workspace" / "logs"
LOG_PATH = LOG_DIR / "librarian-weekly.log"
SKILL_SUGGESTIONS_PATH = HOME / "openclaw-workspace" / "memory" / "skill-suggestions.md"

WINDOW_DAYS = 7
PATTERN_MIN_COUNT = 2  # surface any category with ≥ this many incidents


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(f"[{iso_now()}] {msg}\n")


def parse_ts(value) -> _dt.datetime | None:
    """Parse an ISO8601 or epoch timestamp; return naive-UTC datetime or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return _dt.datetime.fromtimestamp(value, _dt.timezone.utc).replace(tzinfo=None)
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        # Strip trailing Z if present
        s = value.rstrip("Z").replace("+00:00", "")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return _dt.datetime.strptime(s[: len(s) if len(s) < 30 else 26], fmt)
            except ValueError:
                continue
    return None


def load_incidents(path: Path | None = None) -> list[dict]:
    if path is None:
        path = INCIDENTS_PATH  # resolved at call time so tests can monkeypatch
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def filter_window(incidents: list[dict], window_days: int = WINDOW_DAYS,
                  now: _dt.datetime | None = None) -> list[dict]:
    now = now or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    cutoff = now - _dt.timedelta(days=window_days)
    out = []
    for inc in incidents:
        ts = parse_ts(inc.get("timestamp"))
        if ts is None:
            continue
        if ts >= cutoff:
            out.append(inc)
    return out


def group_patterns(incidents: list[dict], min_count: int = PATTERN_MIN_COUNT) -> list[dict]:
    """Group incidents by `error_category` (falling back to `category`).

    Returns a list of pattern dicts sorted by count desc, filtered to
    count >= min_count. Each pattern has:
      category, count, earliest, latest, summaries (unique), most_recent
    """
    by_cat: dict[str, list[dict]] = collections.defaultdict(list)
    for inc in incidents:
        cat = inc.get("error_category") or inc.get("category") or "other"
        by_cat[cat].append(inc)

    patterns = []
    for cat, items in by_cat.items():
        if len(items) < min_count:
            continue
        items_sorted = sorted(items, key=lambda x: parse_ts(x.get("timestamp")) or _dt.datetime.min)
        summaries = []
        for it in items_sorted:
            s = it.get("error_summary") or it.get("description") or "(no summary)"
            if s not in summaries:
                summaries.append(s)
        patterns.append({
            "category": cat,
            "count": len(items),
            "earliest": items_sorted[0].get("timestamp"),
            "latest": items_sorted[-1].get("timestamp"),
            "summaries": summaries[:5],  # cap at 5 unique summaries
            "most_recent": items_sorted[-1],
        })
    patterns.sort(key=lambda p: p["count"], reverse=True)
    return patterns


def render_report(patterns: list[dict], window_days: int,
                  total_scanned: int, in_window: int) -> str:
    lines = [
        "---",
        "name: Librarian weekly patterns (auto-generated)",
        "description: Weekly pattern report of recurring incidents — regenerated every Sunday 06:00 by com.openclaw.librarian.weekly.plist",
        "type: feedback",
        "---",
        "",
        f"**Generated:** {iso_now()}",
        f"**Window:** last {window_days} days",
        f"**Incidents scanned:** {total_scanned} total, {in_window} in window",
        f"**Threshold:** patterns with ≥{PATTERN_MIN_COUNT} incidents",
        "",
    ]
    if not patterns:
        lines.append("## No recurring patterns this week ✅")
        lines.append("")
        lines.append("No error category had ≥2 incidents in the last 7 days.")
        lines.append("")
        lines.append("**How to apply:** Nothing to enforce this week. Keep shipping.")
        return "\n".join(lines) + "\n"

    lines.append(f"## {len(patterns)} recurring pattern(s) flagged")
    lines.append("")
    lines.append("These categories recurred within the last 7 days and should be")
    lines.append("treated as HIGH-severity gaps by Auditor/Quality until the root")
    lines.append("cause is addressed (see 'How to apply' per pattern below).")
    lines.append("")
    for i, p in enumerate(patterns, 1):
        lines.append(f"### {i}. `{p['category']}` — {p['count']} incidents")
        lines.append("")
        lines.append(f"- **Earliest:** {p['earliest']}")
        lines.append(f"- **Latest:** {p['latest']}")
        lines.append("- **Unique summaries seen:**")
        for s in p["summaries"]:
            lines.append(f"  - {s}")
        mr = p["most_recent"]
        root_cause = mr.get("root_cause", "(not recorded)")
        prevention = mr.get("prevention", "(not recorded)")
        lines.append("")
        lines.append(f"**Most recent root cause:** {root_cause}")
        lines.append("")
        lines.append(f"**Most recent prevention:** {prevention}")
        lines.append("")
        lines.append("**Why this matters:** A recurring category means the previous prevention")
        lines.append("did not stick. Planner must incorporate a new constraint; Auditor must")
        lines.append("reject any plan that does not address it; Coder must implement it as a")
        lines.append("code-level guard.")
        lines.append("")
        lines.append(f"**How to apply:** Treat any new task touching `{p['category']}` as a")
        lines.append("higher-risk domain. Include an explicit verification step in the plan")
        lines.append("and a test in the implementation. Flag in `### Applied Lessons`.")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_skill_suggestion(patterns: list[dict]) -> None:
    """Append a one-line weekly summary to memory/skill-suggestions.md."""
    if not patterns:
        line = f"[{iso_now()}] weekly scan: no recurring patterns ✅\n"
    else:
        cats = ", ".join(f"{p['category']}×{p['count']}" for p in patterns[:5])
        line = f"[{iso_now()}] weekly scan: {len(patterns)} patterns → {cats}\n"
    SKILL_SUGGESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SKILL_SUGGESTIONS_PATH.exists():
        SKILL_SUGGESTIONS_PATH.write_text(
            "# skill-suggestions.md — Librarian weekly scan summary\n\n"
            "Appended by `scripts/librarian_weekly.py`. One line per weekly run.\n\n"
        )
    with open(SKILL_SUGGESTIONS_PATH, "a") as f:
        f.write(line)


def main(argv: list[str] | None = None) -> int:
    try:
        log("─── Librarian weekly scan starting ───")
        incidents = load_incidents()
        in_window = filter_window(incidents)
        patterns = group_patterns(in_window)
        report = render_report(patterns, WINDOW_DAYS, len(incidents), len(in_window))
        atomic_write(REPORT_PATH, report)
        append_skill_suggestion(patterns)
        log(f"scanned={len(incidents)} in_window={len(in_window)} patterns={len(patterns)} report={REPORT_PATH}")
        log("─── Librarian weekly scan complete ───")
        print(f"Wrote {REPORT_PATH} ({len(patterns)} patterns from {len(in_window)} in-window incidents)")
        return 0
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        print(f"librarian_weekly FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
