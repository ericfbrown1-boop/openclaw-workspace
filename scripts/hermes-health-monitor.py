#!/usr/bin/env python3
"""
Hermes Supervisor — OpenClaw Health Monitor (Phase 2)
Runs as a Python script (Hermes cron requires Python, not bash).
Checks gateway health, auto-recovers after 3 consecutive failures.
Outputs structured status text — injected as context for the Hermes cron LLM.
"""

import fcntl
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".openclaw/workspace/memory/hermes-supervisor.log"
STATE_FILE = Path.home() / ".openclaw/workspace/memory/hermes-health-state.json"
LOCK_FILE = Path.home() / ".openclaw/workspace/memory/hermes-health-state.lock"
MAX_FAILURES = 3
MAX_RECOVERY_ATTEMPTS = 3
GW_LOG = Path.home() / ".openclaw/logs/gateway.log"


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Rotate if > 5MB
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5_000_000:
        rotated = LOG_FILE.with_suffix(".log.1")
        LOG_FILE.rename(rotated)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts()}] {msg}\n")


def load_state() -> dict:
    """Load state with file locking to prevent race conditions."""
    default = {
        "consecutive_failures": 0,
        "recovery_attempts": 0,
        "last_check": None,
        "last_status": "unknown",
        "last_recovery": None,
        "total_checks": 0,
        "total_recoveries": 0,
        "learning_log": [],
    }
    if not STATE_FILE.exists():
        return default
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def save_state(state: dict):
    """Save state atomically with file locking."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Another process has the lock — wait up to 3 seconds
            try:
                fcntl.flock(lock, fcntl.LOCK_EX)
            except OSError:
                pass  # Best-effort — write anyway

        tmp = STATE_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2))
        tmp.rename(STATE_FILE)

        try:
            fcntl.flock(lock, fcntl.LOCK_UN)
        except OSError:
            pass


def run(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    """Run a subprocess, return (success, combined output)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, str(e)


def check_gateway() -> tuple[bool, str]:
    """Check 1: Is OpenClaw gateway process running?"""
    ok, out = run(["openclaw", "gateway", "status"], timeout=8)
    if "running" in out.lower():
        return True, "running"
    return False, f"not running ({out[:100]})"


def check_http_probe() -> tuple[bool, str]:
    """Check 2: HTTP probe to gateway dashboard."""
    ok, out = run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5",
         "http://127.0.0.1:18789/"],
        timeout=8,
    )
    if ok and out.strip() in ("200", "301", "302", "404"):
        return True, f"http {out.strip()}"
    return False, f"probe failed (code={out.strip()[:20]})"


def check_recent_errors() -> tuple[bool, str]:
    """Check 3: Error spike in gateway log (last 200 lines)."""
    if not GW_LOG.exists():
        return True, "no log file (ok)"
    try:
        lines = GW_LOG.read_text(errors="replace").splitlines()[-200:]
        error_terms = ["fatal", "crash", "uncaughtexception", "sigterm killed"]
        count = sum(
            1 for l in lines
            if any(t in l.lower() for t in error_terms)
        )
        if count > 5:
            return False, f"{count} error lines in last 200"
        return True, f"{count} errors (ok)"
    except OSError:
        return True, "log unreadable (skipped)"


def attempt_recovery(state: dict) -> dict:
    """Try to restart the OpenClaw gateway and verify."""
    attempt_num = state.get("recovery_attempts", 0) + 1
    state["recovery_attempts"] = attempt_num
    log(f"[RECOVERY] Attempt #{attempt_num} — restarting OpenClaw gateway...")
    t_start = time.time()

    ok, out = run(["openclaw", "gateway", "restart"], timeout=30)
    log(f"[RECOVERY] Restart output: {out[:200]}")

    time.sleep(12)  # Give it time to come up

    gw_ok, gw_msg = check_gateway()
    elapsed = int(time.time() - t_start)

    if gw_ok:
        log(f"[RECOVERY] SUCCESS in {elapsed}s")
        state["consecutive_failures"] = 0
        state["recovery_attempts"] = 0
        state["last_recovery"] = ts()
        state["total_recoveries"] = state.get("total_recoveries", 0) + 1
        learning = state.get("learning_log", [])
        learning.append({
            "timestamp": ts(),
            "recovery_time_seconds": elapsed,
            "attempt": attempt_num,
        })
        state["learning_log"] = learning[-50:]
    else:
        log(f"[RECOVERY] FAILED after {elapsed}s — gateway still {gw_msg}")

    return state


def send_telegram_alert(msg: str):
    """Write escalation to a file OpenClaw's monitor agent watches."""
    alert_file = Path.home() / ".openclaw/workspace/memory/hermes-escalation.txt"
    try:
        with open(alert_file, "a") as f:
            f.write(f"[{ts()}] ESCALATION: {msg}\n")
        log(f"[ESCALATION_NOTICE] Written to {alert_file}")
    except OSError as e:
        log(f"[ESCALATION_NOTICE] Failed to write alert: {e}")


def main():
    state = load_state()

    # Run all 3 health checks
    gw_ok, gw_msg = check_gateway()
    http_ok, http_msg = check_http_probe()
    err_ok, err_msg = check_recent_errors()

    overall_healthy = gw_ok and http_ok and err_ok
    failures = state.get("consecutive_failures", 0)

    if overall_healthy:
        state["consecutive_failures"] = 0
        state["recovery_attempts"] = 0
        state["last_status"] = "healthy"
        state["last_check"] = ts()
        state["total_checks"] = state.get("total_checks", 0) + 1
        save_state(state)

        total = state["total_checks"]
        # Only log every 10th healthy check
        if total % 10 == 0:
            log(f"[STATUS] OK — gateway={gw_msg} probe={http_msg} errors={err_msg} (check #{total})")

        # Output for Hermes cron LLM context (only on 10th check to save tokens)
        if total % 10 == 0:
            print(f"[STATUS] OK — gateway={gw_msg} probe={http_msg} errors={err_msg} (check #{total})")
        # Else output nothing — no LLM call needed for healthy state
        return

    # Unhealthy path
    failures += 1
    state["consecutive_failures"] = failures
    state["last_status"] = "unhealthy"
    state["last_check"] = ts()
    state["total_checks"] = state.get("total_checks", 0) + 1

    reasons = []
    if not gw_ok:
        reasons.append(f"gateway: {gw_msg}")
    if not http_ok:
        reasons.append(f"probe: {http_msg}")
    if not err_ok:
        reasons.append(f"errors: {err_msg}")
    reason_str = "; ".join(reasons)

    log(f"[ALERT] Failure #{failures}/3 — {reason_str}")

    if failures >= MAX_FAILURES:
        recovery_attempts = state.get("recovery_attempts", 0)
        if recovery_attempts < MAX_RECOVERY_ATTEMPTS:
            state = attempt_recovery(state)
        else:
            msg = f"Recovery exhausted ({MAX_RECOVERY_ATTEMPTS} attempts). Manual intervention required. Last failure: {reason_str}"
            log(f"[ESCALATION_NOTICE] {msg}")
            send_telegram_alert(msg)
            print(f"[ESCALATION_NOTICE] {msg}")

    save_state(state)

    # Always output alerts so Hermes LLM gets context
    print(f"[ALERT] OpenClaw failure #{failures} — {reason_str}")
    if failures >= MAX_FAILURES:
        print(f"[RECOVERY] Attempted restart — see hermes-supervisor.log for result")


if __name__ == "__main__":
    main()
