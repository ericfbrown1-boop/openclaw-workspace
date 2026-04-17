#!/usr/bin/env python3
"""
Hermes Supervisor — Quality Review Gate (Phase 3)
Self-contained: no CLI args needed. Finds and reviews today's daily briefing.
Stdout is injected as context for the Hermes supervisor cron LLM.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".openclaw/workspace/memory/hermes-supervisor.log"
REVIEW_STATE = Path.home() / ".openclaw/workspace/memory/hermes-review-state.json"
MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
WORKSPACE_DIR = Path.home() / ".openclaw/workspace"


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5_000_000:
        LOG_FILE.rename(LOG_FILE.with_suffix(".log.1"))
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts()}] {msg}\n")


def load_state() -> dict:
    if REVIEW_STATE.exists():
        try:
            return json.loads(REVIEW_STATE.read_text())
        except Exception:
            pass
    return {"reviews_total": 0, "reviews_passed": 0, "reviews_failed": 0, "last_review": None}


def save_state(state: dict):
    REVIEW_STATE.write_text(json.dumps(state, indent=2))


def find_todays_briefing() -> Path | None:
    """Find today's daily briefing, with fallback to yesterday (briefing may arrive late)."""
    for days_back in [0, 1]:
        from datetime import timedelta
        target = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Check all common naming patterns
        candidates = [
            MEMORY_DIR / f"daily-briefing-{target}.md",
            MEMORY_DIR / f"briefing-{target}.md",
            WORKSPACE_DIR / f"daily-briefing-{target}.md",
        ]
        for c in candidates:
            if c.exists():
                return c

        # Scan both dirs for any file matching the date
        for d in [MEMORY_DIR, WORKSPACE_DIR]:
            if d.exists():
                for f in d.iterdir():
                    if f.is_file() and target in f.name and "briefing" in f.name.lower():
                        return f

    return None


def review_content(content: str, filename: str) -> dict:
    issues = []
    warnings = []
    content_lower = content.lower()
    lines = content.split("\n")

    # 1. Length check
    if len(content.strip()) < 500:
        issues.append(f"Too short ({len(content)} chars — minimum 500)")
    elif len(content.strip()) < 1000:
        warnings.append(f"Brief content ({len(content)} chars)")

    # 2. Placeholder / unavailable detection
    na_phrases = [
        "not available", "data not found", "unable to retrieve",
        "placeholder", "lorem ipsum", "[insert", "coming soon",
    ]
    na_count = sum(content_lower.count(p) for p in na_phrases)
    # TBD/TODO/N/A are too common in legitimate content — just warn
    todo_count = content_lower.count("todo") + content_lower.count("fixme")
    if na_count > 5:
        issues.append(f"Too many unavailable/placeholder entries ({na_count})")
    elif na_count > 2:
        warnings.append(f"Several placeholder entries ({na_count})")
    if todo_count > 0:
        warnings.append(f"Contains {todo_count} TODO/FIXME markers")

    # 3. Briefing section completeness (only for briefing files)
    if "briefing" in filename.lower() or "daily" in filename.lower():
        expected = ["gmail", "calendar", "claude", "competitive", "system health"]
        missing = [s for s in expected if s not in content_lower]
        if len(missing) > 2:
            issues.append(f"Missing {len(missing)} briefing sections: {', '.join(missing)}")
        elif missing:
            warnings.append(f"Missing sections: {', '.join(missing)}")

    # 4. Unclosed code blocks
    if content.count("```") % 2 != 0:
        issues.append(f"Unclosed code block ({content.count('```')} backtick groups)")

    # 5. Duplicate section headers
    headers = [line.strip() for line in lines if line.strip().startswith("#")]
    seen, dupes = set(), []
    for h in headers:
        if h in seen:
            dupes.append(h)
        seen.add(h)
    if dupes:
        warnings.append(f"Duplicate headers: {dupes[:3]}")

    # 6. Leaked error messages — only flag exact patterns, avoid false positives
    hard_error_patterns = [
        r"traceback \(most recent",
        r"syntaxerror:",
        r"importerror:",
        r"http 5\d\d",
        r"connection refused",
    ]
    for pattern in hard_error_patterns:
        if re.search(pattern, content_lower):
            issues.append(f"Possible leaked error: matched '{pattern}'")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "stats": {
            "chars": len(content),
            "lines": len(lines),
            "headers": len(headers),
            "placeholders": na_count,
        },
    }


def main():
    state = load_state()
    briefing = find_todays_briefing()

    if not briefing:
        log("[REVIEW] No daily briefing found (checked today + yesterday)")
        print("[REVIEW] NO_BRIEFING — No daily briefing file found for today or yesterday.")
        print("Action: Verify the briefing cron ran successfully. Check memory/ directory.")
        return

    try:
        content = briefing.read_text(errors="replace")
    except OSError as e:
        log(f"[REVIEW] Failed to read briefing: {e}")
        print(f"[REVIEW] ERROR — Could not read {briefing}: {e}")
        return

    result = review_content(content, briefing.name)
    state["reviews_total"] = state.get("reviews_total", 0) + 1
    state["last_review"] = ts()
    state["last_file"] = str(briefing)

    if result["passed"]:
        state["reviews_passed"] = state.get("reviews_passed", 0) + 1
        log(f"[REVIEW] PASS — {briefing.name} ({result['stats']['chars']} chars, {result['stats']['placeholders']} placeholders)")
        print(f"[REVIEW] PASS — {briefing.name}")
        print(f"Stats: {result['stats']}")
        if result["warnings"]:
            print(f"Warnings (non-blocking): {'; '.join(result['warnings'])}")
    else:
        state["reviews_failed"] = state.get("reviews_failed", 0) + 1
        log(f"[REVIEW] FAIL — {briefing.name} — {'; '.join(result['issues'])}")
        print(f"[REVIEW] FAIL — {briefing.name}")
        print(f"Issues: {'; '.join(result['issues'])}")
        if result["warnings"]:
            print(f"Warnings: {'; '.join(result['warnings'])}")
        print(f"Stats: {result['stats']}")
        print("Action required: Regenerate or manually fix the briefing before delivery.")

    save_state(state)


if __name__ == "__main__":
    main()
