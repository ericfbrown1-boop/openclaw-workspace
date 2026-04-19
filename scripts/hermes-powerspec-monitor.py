#!/usr/bin/env python3
"""
Hermes Supervisor — PowerSpec PC Monitor (Docker + Services Health)
Runs every 5 minutes via Hermes cron.
Checks: Tailscale reachability, SSH, Docker Desktop, key containers.
Auto-recovers: Restarts Docker Desktop if down.
Stdout injected as LLM context — only outputs on problem or every 20th check.

Services monitored:
  - Firecrawl (port 3002)
  - ContractAnalyzer API (port 8000)
  - FinancialReportApp API (port 8001)
"""

import json
import logging
import logging.handlers
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE   = Path.home() / ".openclaw/workspace/memory/hermes-supervisor.log"
STATE_FILE = Path.home() / ".openclaw/workspace/memory/hermes-powerspec-state.json"

TAILSCALE   = "/usr/local/bin/tailscale"
SSH_HOST    = "Eric Brown@100.81.21.114"
SSH_OPTS    = ["-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no"]

EXPECTED_CONTAINERS = ["firecrawl", "contractanalyzer", "financialreportapp"]
DOCKER_DESKTOP_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

STATE_DEFAULT = {
    "total_checks": 0,
    "consecutive_failures": 0,
    "docker_restarts": 0,
    "last_check": None,
    "last_status": "unknown",
    "last_docker_restart": None,
    "containers_last_seen": {},
}


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_logger() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("hermes-powerspec")
    if logger.handlers:
        return logger
    h = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=2)
    h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    return logger


_log = _build_logger()


def log(msg: str):
    _log.info(f"[{ts()}] {msg}")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return {**STATE_DEFAULT, **json.loads(STATE_FILE.read_text())}
        except Exception:
            pass
    return dict(STATE_DEFAULT)


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def run(cmd: list, timeout: int = 12) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def ssh_run(command: str, timeout: int = 15) -> tuple[bool, str]:
    """Run a command on PowerSpec via SSH."""
    cmd = ["ssh"] + SSH_OPTS + [SSH_HOST, command]
    return run(cmd, timeout=timeout)


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_tailscale() -> tuple[bool, str]:
    _, out = run([TAILSCALE, "ping", "powerspecpc"], timeout=12)
    if "pong" in out.lower():
        # Extract latency
        import re
        m = re.search(r"in (\d+)ms", out)
        latency = f"{m.group(1)}ms" if m else "ok"
        return True, latency
    return False, f"no pong ({out[:80]})"


def check_ssh() -> tuple[bool, str]:
    ok, out = ssh_run("echo ONLINE", timeout=10)
    if ok and "ONLINE" in out:
        return True, "ok"
    return False, f"failed ({out[:80]})"


def check_docker() -> tuple[bool, list[str]]:
    """Returns (docker_running, list_of_running_container_names)."""
    ok, out = ssh_run(
        "powershell -NonInteractive -Command \"docker ps --format '{{.Names}}:{{.Status}}'\"",
        timeout=15,
    )
    if not ok or "failed to connect" in out.lower() or "cannot find" in out.lower():
        return False, []

    containers = []
    for line in out.strip().splitlines():
        if ":" in line:
            name, status = line.split(":", 1)
            if "up" in status.lower():
                containers.append(name.strip().lower())
    return True, containers


def restart_docker_desktop() -> bool:
    """Attempt to start Docker Desktop on PowerSpec."""
    log("[POWERSPEC] Attempting Docker Desktop restart...")
    ok, out = ssh_run(
        f"powershell -NonInteractive -Command \"Start-Process '{DOCKER_DESKTOP_PATH}'\"",
        timeout=15,
    )
    log(f"[POWERSPEC] Docker Desktop launch: ok={ok} out={out[:100]}")
    # Give it time to start WSL2 backend
    time.sleep(45)
    docker_ok, containers = check_docker()
    return docker_ok


def check_services(containers: list[str]) -> dict[str, bool]:
    """Check which expected containers are running."""
    results = {}
    for expected in EXPECTED_CONTAINERS:
        results[expected] = any(expected.lower() in c for c in containers)
    return results


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    state = load_state()
    state["total_checks"] = state.get("total_checks", 0) + 1
    state["last_check"] = ts()

    issues = []
    recovered = []

    # Check 1: Tailscale
    ts_ok, ts_msg = check_tailscale()
    if not ts_ok:
        issues.append(f"Tailscale: ❌ {ts_msg}")
        log(f"[POWERSPEC] Tailscale FAIL: {ts_msg}")
        state["last_status"] = "tailscale_down"
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        save_state(state)
        print(f"[POWERSPEC] ❌ TAILSCALE DOWN — {ts_msg}")
        print("Action: PowerSpec is unreachable. Tailscale may need to be restarted on the PC manually.")
        return

    # Check 2: SSH
    ssh_ok, ssh_msg = check_ssh()
    if not ssh_ok:
        issues.append(f"SSH: ❌ {ssh_msg}")
        log(f"[POWERSPEC] SSH FAIL: {ssh_msg}")
        state["last_status"] = "ssh_down"
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        save_state(state)
        print(f"[POWERSPEC] ❌ SSH DOWN — {ssh_msg}")
        print("Action: SSH service may have stopped. Try restarting from PC: Restart-Service sshd")
        return

    # Check 3: Docker
    docker_ok, containers = check_docker()

    if not docker_ok:
        log("[POWERSPEC] Docker Desktop not running — attempting auto-restart")
        restart_attempts = state.get("docker_restarts", 0)

        if restart_attempts < 3:
            restarted = restart_docker_desktop()
            state["docker_restarts"] = restart_attempts + 1
            state["last_docker_restart"] = ts()

            if restarted:
                # Re-check containers after restart
                docker_ok, containers = check_docker()
                recovered.append("Docker Desktop (auto-restarted)")
                log(f"[POWERSPEC] Docker restart SUCCESS — containers now running: {containers}")
            else:
                issues.append("Docker Desktop: ❌ Down, restart failed")
                log("[POWERSPEC] Docker restart FAILED")
        else:
            issues.append(f"Docker Desktop: ❌ Down, {restart_attempts} restart attempts failed")
            log(f"[POWERSPEC] Docker restart exhausted ({restart_attempts} attempts)")

    # Check 4: Individual containers
    if docker_ok:
        state["docker_restarts"] = 0  # Reset on success
        svc_status = check_services(containers)

        missing = [svc for svc, running in svc_status.items() if not running]
        running = [svc for svc, running in svc_status.items() if running]

        state["containers_last_seen"] = {
            svc: ts() for svc in running
        } | state.get("containers_last_seen", {})

        if missing:
            issues.append(f"Containers DOWN: {', '.join(missing)}")
            log(f"[POWERSPEC] Containers not running: {missing}")

            # Attempt docker compose up for missing services
            for svc in missing:
                log(f"[POWERSPEC] Attempting to start {svc}...")
                ok, out = ssh_run(
                    f"powershell -NonInteractive -Command \"cd ~; docker start $(docker ps -aq --filter name={svc}) 2>&1\"",
                    timeout=20,
                )
                if ok:
                    recovered.append(f"{svc} container (auto-started)")
                    log(f"[POWERSPEC] {svc} start: {out[:100]}")

    # ── Determine overall status ────────────────────────────────────────────────
    if issues:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_status"] = "degraded"
    else:
        state["consecutive_failures"] = 0
        state["last_status"] = "healthy"

    save_state(state)
    total = state["total_checks"]

    # Only output to Hermes LLM on: problems, recoveries, or every 20th check
    if issues or recovered or total % 20 == 0:
        ts_latency = ts_msg if ts_ok else "N/A"
        container_status = check_services(containers) if docker_ok else {s: False for s in EXPECTED_CONTAINERS}
        container_line = " | ".join(
            f"{s}: {'✅' if ok else '❌'}" for s, ok in container_status.items()
        )

        print(f"[POWERSPEC] Tailscale: ✅ {ts_latency} | SSH: ✅ | Docker: {'✅' if docker_ok else '❌'}")
        print(f"[POWERSPEC] {container_line}")

        if recovered:
            print(f"[POWERSPEC] ✅ Auto-recovered: {', '.join(recovered)}")
        if issues:
            for issue in issues:
                print(f"[POWERSPEC] ⚠️  {issue}")
            print("[POWERSPEC] Action: Review above issues. If Docker is persistently down, manual intervention may be required on the PC.")
        elif not issues:
            print(f"[POWERSPEC] All systems healthy (check #{total})")

    log(f"[POWERSPEC] Check #{total} complete — status={state['last_status']} docker={docker_ok} containers={containers}")


if __name__ == "__main__":
    main()
