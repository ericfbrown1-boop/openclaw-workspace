#!/usr/bin/env python3
"""jarvis_pipeline.py — External orchestrator for the Jarvis 8-agent SDLC pipeline.

Works around the upstream openclaw CLI one-turn limit (acp-cli-DsBOatVe.js
finishPrompt resolves turn on state=final before tool calls execute).
Drives each stage sequentially via `openclaw agent --agent <id>` and feeds
outputs forward.

Usage:
    jarvis_pipeline.py run <task-id> [--resume] [--skip-stage NAME] [--full-agent]
    jarvis_pipeline.py status <task-id>
    jarvis_pipeline.py reset <task-id>
    jarvis_pipeline.py list

Stages (in order):
    researcher  → outputs research brief
    planner     → Opus 4.6, writes PLAN.md
    auditor     → Grok 4.20 Beta, appends review to PLAN.md
    coder       → Sonnet 4.6, implements + commits
    quality     → Grok 4.20 Beta hybrid: runs verificationCmd (deterministic)
                  + LLM output-correctness review; halts on either fail
    monitor     → deterministic: writes incident if any stage failed
    conductor   → deterministic: dual-writes task status to both tasks.json stores

No external dependencies — stdlib only (argparse, subprocess, json, fcntl,
pathlib, datetime). Runs under any launchd PATH.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Paths & constants
# ──────────────────────────────────────────────────────────────────────────────

HOME = Path.home()
OPENCLAW_WORKSPACE = HOME / "openclaw-workspace"
OPENCLAW_WORKSPACE_MIRROR = HOME / ".openclaw" / "workspace"  # linked copy
PIPELINE_STATE_PATH = OPENCLAW_WORKSPACE / "memory" / "pipeline-state.json"
PIPELINE_LOCK_PATH = OPENCLAW_WORKSPACE / "memory" / "pipeline-state.json.lock"
OUTPUTS_DIR = OPENCLAW_WORKSPACE / "pipeline-outputs"
INCIDENTS_PATH = OPENCLAW_WORKSPACE / "memory" / "incidents.jsonl"
TASKS_OPENCLAW = OPENCLAW_WORKSPACE / "tasks.json"
TASKS_OPENCLAW_MIRROR = OPENCLAW_WORKSPACE_MIRROR / "tasks.json"
TASKS_MISSION_CONTROL = HOME / "JarvisMissionControl" / "backend" / "data" / "tasks.json"

STAGES = ["researcher", "planner", "auditor", "coder", "quality", "monitor", "conductor"]
LLM_STAGES = {"researcher", "planner", "auditor", "coder", "quality"}  # dispatch to openclaw
DEFAULT_STAGE_TIMEOUT_SEC = {
    "researcher": 600,
    "planner": 1200,
    "auditor": 600,
    "coder": 1800,
    "quality": 600,
}

# Mission Control integration — all pipeline runs are visible on the dashboard
# in real time via the MC REST API. See `_mc_*` helpers below for details.
MISSION_CONTROL_URL = os.environ.get("MISSION_CONTROL_URL", "http://localhost:3001")
MISSION_CONTROL_TIMEOUT_SEC = 5  # fail fast — we don't block the pipeline on MC

# PowerSpec node dispatch (Option C, 2026-04-11) — lets stage_coder run Claude
# Code on the paired PowerSpec Windows node via openclaw's agent `exec` tool
# with host=<nodeId>. See `_dispatch_coder_powerspec` + DELEGATION.md.
#
# Hybrid architecture: SSH is used for plumbing (staging prompt files, reading
# output, capturing git sha) because it's simpler and proven-reliable. The
# actual Claude Code invocation — the WORKLOAD that matters for Option C —
# goes through `openclaw agent --agent main` + exec tool with host=<nodeId>.
# This gives us the native-nodes path for the LLM work without getting tangled
# in exec-tool quoting for the infrastructure bits.
POWERSPEC_NODE_NAME = "PowerSpec"
POWERSPEC_SSH_USER = "Eric Brown"   # Windows user, space-quoted at use sites
POWERSPEC_SSH_ADDR = "100.81.21.114"
POWERSPEC_REMOTE_BASE_DIR = r"C:\Users\Eric Brown\repos"  # where per-task dirs live
POWERSPEC_CLAUDE_CMD = r"claude.cmd"
POWERSPEC_EXEC_TIMEOUT_SEC = 1800  # 30 min — generous for long Coder runs


def _powerspec_ssh(remote_cmd: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a shell command on PowerSpec via SSH. Used for plumbing (file transfer,
    dir setup, git sha capture). The actual Claude Code invocation uses
    `openclaw nodes` via the agent exec tool — see _dispatch_coder_powerspec.
    """
    return subprocess.run(
        [
            "ssh",
            "-o", f'User="{POWERSPEC_SSH_USER}"',
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=accept-new",
            POWERSPEC_SSH_ADDR,
            remote_cmd,
        ],
        capture_output=True, text=True, timeout=timeout,
    )

# Progress percentages per stage, keyed by stage name → (start%, done%).
# Chosen so each major LLM stage has a visible range and monitor/conductor
# push us to 100%.
STAGE_PROGRESS = {
    "researcher": (5, 15),
    "planner":    (20, 35),
    "auditor":    (40, 50),
    "coder":      (55, 75),
    "quality":    (80, 90),
    "monitor":    (92, 95),
    "conductor":  (96, 100),
}

# Librarian memory — Auditor (and optionally Planner/Coder) reads these
# files before reviewing, so past lessons are enforced as part of the
# adversarial review. See DELEGATION.md "Learn Before Review" rule.
LIBRARIAN_MEMORY_ROOTS = [
    Path.home() / ".claude" / "projects",  # all <project>/memory/*.md
]
LIBRARIAN_MEMORY_MAX_BYTES = 250_000  # safety cap; Grok 4.20 Beta has 2M ctx
LIBRARIAN_MEMORY_SKIP_NAMES = {"MEMORY.md"}  # index files, not content

# External context hook — user-provided knowledge injection for Researcher + Planner.
# See `external_context_hook.py.example` in this dir for the interface + integration
# notes (Obsidian, karpathy/autoresearch, etc.). Hook is discovered at call-time:
#   1. Python module at EXTERNAL_CONTEXT_HOOK_PATH, imported dynamically
#   2. OR shell command in env var JARVIS_EXTERNAL_CONTEXT_CMD (stdin=JSON, stdout=text)
#   3. Otherwise return empty string (no-op)
EXTERNAL_CONTEXT_HOOK_PATH = Path(__file__).parent / "external_context_hook.py"
EXTERNAL_CONTEXT_MAX_BYTES = 500_000  # safety cap
EXTERNAL_CONTEXT_TIMEOUT_SEC = 120

# ──────────────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────────────


class PipelineError(Exception):
    """Base class for all orchestrator errors."""


class DispatchError(PipelineError):
    """Raised when an openclaw agent dispatch fails or times out."""


class QualityGateFailed(PipelineError):
    """Raised when the verificationCmd exits non-zero OR the quality LLM rejects."""


class AuditorRejected(PipelineError):
    """Raised when Auditor returns REJECTED verdict."""


class TaskNotFound(PipelineError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def walk_for_key(obj: Any, key: str) -> Any:
    """Recursively search a nested dict/list tree for the first value at `key`."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = walk_for_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for i in obj:
            r = walk_for_key(i, key)
            if r is not None:
                return r
    return None


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically via tmp + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with open(path) as f:
        return json.load(f)


def load_external_context(task: dict, stage: str) -> str:
    """Call the user-provided external context hook if present.

    Intended for injecting knowledge from an Obsidian vault + autoresearch
    (karpathy/autoresearch-style) backend, or any other per-task knowledge
    source the user wants. Called by `stage_researcher` and `stage_planner`.

    Security model (post-review C1 fix 2026-04-11): the hook is ALWAYS run
    in an isolated subprocess — never imported via `exec_module` into the
    orchestrator process. This contains any code execution in the hook to
    its own process, killable on timeout, and unable to mutate orchestrator
    state. The hook file must implement a `__main__` block that reads
    `{"task": ..., "stage": ...}` from stdin and writes the context to
    stdout (see `external_context_hook.py.example`).

    Discovery order:
      1. Python subprocess: `python3 <EXTERNAL_CONTEXT_HOOK_PATH>` with
         `{"task": {...}, "stage": "..."}` on stdin
      2. Shell command in env var `JARVIS_EXTERNAL_CONTEXT_CMD` — receives
         the same JSON on stdin, must print context to stdout on exit 0
      3. Otherwise return empty string

    Fail-safe: any subprocess error or timeout → logged, returns empty
    string. Pipeline never breaks because a knowledge source is down.

    Task opt-out: `task["externalContext"]["enabled"] == false` skips the
    hook entirely.

    Size cap: return value is truncated to `EXTERNAL_CONTEXT_MAX_BYTES`.

    See `scripts/external_context_hook.py.example` for the hook template.
    """
    ext_cfg = task.get("externalContext") or {}
    if ext_cfg.get("enabled") is False:
        return ""

    payload = json.dumps({"task": task, "stage": stage})

    # Path 1: Python subprocess hook (isolated — cannot touch orchestrator state)
    if EXTERNAL_CONTEXT_HOOK_PATH.exists():
        try:
            proc = subprocess.run(
                [sys.executable, str(EXTERNAL_CONTEXT_HOOK_PATH)],
                input=payload,
                capture_output=True,
                text=True,
                timeout=EXTERNAL_CONTEXT_TIMEOUT_SEC,
            )
            if proc.returncode == 0:
                return _truncate_context(proc.stdout)
            _log_hook_error(
                f"Python hook exited {proc.returncode}: {(proc.stderr or '')[:200]}"
            )
            return ""
        except subprocess.TimeoutExpired:
            _log_hook_error(f"Python hook timed out after {EXTERNAL_CONTEXT_TIMEOUT_SEC}s")
            return ""
        except (OSError, ValueError) as e:
            _log_hook_error(f"Python hook subprocess: {e!r}")
            return ""

    # Path 2: shell command hook
    cmd = os.environ.get("JARVIS_EXTERNAL_CONTEXT_CMD", "").strip()
    if cmd:
        try:
            proc = subprocess.run(
                ["/bin/sh", "-c", cmd],
                input=payload,
                capture_output=True,
                text=True,
                timeout=EXTERNAL_CONTEXT_TIMEOUT_SEC,
            )
            if proc.returncode == 0:
                return _truncate_context(proc.stdout)
            _log_hook_error(f"Shell hook exited {proc.returncode}: {(proc.stderr or '')[:200]}")
        except subprocess.TimeoutExpired:
            _log_hook_error(f"Shell hook timed out after {EXTERNAL_CONTEXT_TIMEOUT_SEC}s")
        except (OSError, ValueError) as e:
            _log_hook_error(f"Shell hook: {e!r}")
    return ""


def _truncate_context(s: str) -> str:
    if len(s) <= EXTERNAL_CONTEXT_MAX_BYTES:
        return s
    return s[:EXTERNAL_CONTEXT_MAX_BYTES] + f"\n\n[…external context truncated at {EXTERNAL_CONTEXT_MAX_BYTES} bytes…]\n"


def _log_hook_error(msg: str) -> None:
    """Append a hook failure line to the orchestrator log (best-effort).

    Post-review H2 fix (2026-04-11): narrowed bare `except Exception` to
    `OSError` — the only realistic failure mode for disk-logging is
    filesystem-related (permission denied, disk full, no such directory).
    Narrower catch means we'll still see and surface any real programming
    error inside this function.
    """
    try:
        log_dir = Path.home() / "openclaw-workspace" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "jarvis-pipeline-hooks.log", "a") as f:
            f.write(f"[{iso_now()}] external_context: {msg}\n")
    except OSError:
        pass  # disk issue — never let a log failure propagate


# ──────────────────────────────────────────────────────────────────────────────
# Mission Control integration
# ──────────────────────────────────────────────────────────────────────────────

def _mc_log(msg: str) -> None:
    """Best-effort logging for MC integration failures.

    Post-review H2 fix: narrowed from bare Exception to OSError.
    """
    try:
        log_dir = Path.home() / "openclaw-workspace" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "jarvis-pipeline-mc.log", "a") as f:
            f.write(f"[{iso_now()}] {msg}\n")
    except OSError:
        pass


def _mc_http(method: str, path: str, body: dict | None = None) -> tuple[int, dict | None]:
    """HTTP request to the Mission Control backend. Fail-safe.

    Returns (status_code, json_body) or (0, None) on any transport error.
    Never raises. Never blocks the pipeline — 5s timeout.

    Post-review H2 fix: narrowed the outer except from `Exception` to
    specific transport/URL/value errors. Programming errors in this
    function will now propagate instead of being silently logged.
    """
    url = f"{MISSION_CONTROL_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=MISSION_CONTROL_TIMEOUT_SEC) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return resp.status, None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()[:200]
        except (OSError, UnicodeDecodeError):
            err_body = ""
        _mc_log(f"{method} {path} → HTTP {e.code} {err_body}")
        return e.code, None
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError) as e:
        _mc_log(f"{method} {path} → {e!r}")
        return 0, None


def _mc_ensure_task(task: dict) -> None:
    """Ensure the task exists in Mission Control. POST if missing, no-op otherwise."""
    tid = task["id"]
    status, _ = _mc_http("GET", f"/tasks/{tid}")
    if status == 200:
        # Task exists — move it to running via PUT
        _mc_http("PUT", f"/tasks/{tid}", {
            "status": "running",
            "progress": 1,
            "update": "Pipeline starting via jarvis_pipeline.py",
        })
        return
    if status == 404:
        payload = {
            "id": tid,
            "title": task.get("title", tid),
            "status": "running",
            "priority": task.get("priority", "medium"),
            "owner": task.get("owner", "jarvis-pipeline"),
            "summary": task.get("summary") or (task.get("objective", "") or "")[:500],
            "progress": 1,
            "etaMinutes": int(task.get("etaMinutes", 25)),
            "agentChain": [],
            "updates": [{"timestamp": iso_now(), "text": "Pipeline starting via jarvis_pipeline.py"}],
        }
        status, _ = _mc_http("POST", "/tasks", payload)
        if status not in (200, 201):
            _mc_log(f"POST /tasks failed (status={status}) — task={tid}")


def _mc_update_stage(task: dict, stage_name: str, phase: str, extra: dict | None = None) -> None:
    """Update Mission Control with a stage transition.

    phase: 'start', 'done', 'failed', 'skipped', 'revising'
    extra: additional fields merged into the PUT body (e.g. completedCommit)

    Post-Option-C (2026-04-11): includes `host` field in the agentChain entry
    so the dashboard can show which machine each stage ran on. For Coder,
    reads `task.execution.coderHost` ("local" | "powerspec"). Other stages
    default to "local".
    """
    tid = task["id"]
    if stage_name in STAGE_PROGRESS:
        start_pct, done_pct = STAGE_PROGRESS[stage_name]
        progress = start_pct if phase in ("start", "revising") else done_pct
    else:
        progress = None

    # Determine which host this stage ran on
    if stage_name == "coder":
        exe = task.get("execution") or {}
        host = exe.get("coderHost", "local")
    else:
        host = "local"

    payload: dict[str, Any] = {}
    if progress is not None:
        payload["progress"] = progress
    if phase == "start":
        payload["agent"] = {
            "agent": stage_name,
            "message": f"{stage_name} running on {host}",
            "host": host,
        }
        payload["update"] = f"[{stage_name}] ▶ running on {host}"
    elif phase == "done":
        payload["update"] = f"[{stage_name}] ✓ completed on {host}"
    elif phase == "failed":
        payload["update"] = f"[{stage_name}] ✗ FAILED on {host}"
    elif phase == "skipped":
        payload["update"] = f"[{stage_name}] ⊘ skipped (already completed)"
    elif phase == "revising":
        payload["update"] = f"[{stage_name}] ⟳ revising on {host} (rejection feedback applied)"
    if extra:
        payload.update(extra)
    if not payload:
        return
    _mc_http("PUT", f"/tasks/{tid}", payload)


def _mc_finalize(task: dict, pstate: dict) -> None:
    """Write final pipeline outcome to Mission Control."""
    tid = task["id"]
    overall_ok = all(pstate["stages"][s]["status"] == "completed" for s in STAGES)
    payload: dict[str, Any] = {
        "status": "completed" if overall_ok else "failed",
        "progress": 100 if overall_ok else pstate["stages"].get(pstate.get("currentStage", "monitor"), {}).get("progress", 0),
        "update": f"Pipeline {'completed' if overall_ok else 'failed'} at {iso_now()}",
    }
    sha = pstate["stages"]["coder"].get("commitSha", "")
    if sha:
        payload["completedCommit"] = sha
    if overall_ok:
        payload["completedAt"] = iso_now()
    _mc_http("PUT", f"/tasks/{tid}", payload)


# Module-level cache for Librarian memory content, keyed by (roots, max_bytes).
# Entry value: (aggregate_mtime, content). See load_librarian_memory.
_LIBRARIAN_MEMORY_CACHE: dict[tuple, tuple[float, str]] = {}


def _librarian_files_and_mtime(roots: list[Path]) -> tuple[list[Path], float]:
    """Scan roots and return (files, max_mtime). Used both to enumerate and
    as the cache key for mtime-based invalidation.
    """
    files: list[Path] = []
    max_mtime = 0.0
    for root in roots:
        if not root.exists():
            continue
        try:
            projects = sorted(root.iterdir())
        except OSError:
            continue
        for project_dir in projects:
            if not project_dir.is_dir():
                continue
            mem_dir = project_dir / "memory"
            if not mem_dir.is_dir():
                continue
            try:
                max_mtime = max(max_mtime, mem_dir.stat().st_mtime)
            except OSError:
                pass
            for p in sorted(mem_dir.glob("*.md")):
                if p.name in LIBRARIAN_MEMORY_SKIP_NAMES:
                    continue
                files.append(p)
                try:
                    max_mtime = max(max_mtime, p.stat().st_mtime)
                except OSError:
                    pass
    return files, max_mtime


def load_librarian_memory(roots: list[Path] | None = None, max_bytes: int = LIBRARIAN_MEMORY_MAX_BYTES) -> str:
    """Read all Librarian memory files from the configured roots and return
    a single concatenated string with headers.

    Scans `<root>/<project>/memory/*.md` one level deep, skipping `MEMORY.md`
    index files. Honors `max_bytes` as a soft cap.

    Post-review M2 fix (2026-04-11): results are cached by (roots, max_bytes)
    with aggregate-mtime invalidation. When Planner, Auditor, and Coder all
    call this in quick succession (one pipeline run), only the first call
    actually hits disk; subsequent calls return the cached content until any
    memory file or memory-dir mtime advances past the cached value.

    Returns empty string if no memory files are found.
    """
    roots = roots if roots is not None else LIBRARIAN_MEMORY_ROOTS
    cache_key = (tuple(str(r) for r in roots), max_bytes)

    files, current_mtime = _librarian_files_and_mtime(roots)

    cached = _LIBRARIAN_MEMORY_CACHE.get(cache_key)
    if cached is not None and cached[0] >= current_mtime and current_mtime > 0:
        return cached[1]

    if not files:
        _LIBRARIAN_MEMORY_CACHE[cache_key] = (current_mtime, "")
        return ""

    chunks: list[str] = []
    total = 0
    truncated = False
    for p in files:
        try:
            content = p.read_text()
        except OSError:
            continue
        # Best-effort project name from path: ~/.claude/projects/<project>/memory/<file>
        try:
            project_name = p.parent.parent.name
        except (AttributeError, IndexError):
            project_name = "?"
        header = f"\n--- FILE: {project_name}/{p.name} ---\n"
        block = header + content + "\n"
        if total + len(block) > max_bytes:
            truncated = True
            break
        chunks.append(block)
        total += len(block)

    if truncated:
        chunks.append(f"\n[…Librarian memory truncated at {max_bytes} bytes…]\n")

    result = "".join(chunks)
    _LIBRARIAN_MEMORY_CACHE[cache_key] = (current_mtime, result)
    return result


def _invalidate_librarian_cache() -> None:
    """Clear the Librarian memory cache. Exposed for tests and for forced
    refresh (e.g., after a manual memory file edit during a long-lived session).
    """
    _LIBRARIAN_MEMORY_CACHE.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline state (read/write with fcntl.flock)
# ──────────────────────────────────────────────────────────────────────────────


class StateLock:
    """Exclusive lock held for the duration of a pipeline run.

    Post-review M4 fix (2026-04-11): opens the lock file with `O_NOFOLLOW`
    via `os.open` to prevent TOCTOU symlink attacks where an attacker could
    place a symlink at the lock path pointing at a sensitive file right
    before the lock is acquired.
    """

    def __init__(self, path: Path):
        self.path = path
        self._fh = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # O_NOFOLLOW: refuse to open if path is a symlink → no TOCTOU race
        # O_CLOEXEC: don't leak the fd to child subprocesses
        flags = os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            fd = os.open(str(self.path), flags, 0o600)
        except OSError as e:
            raise PipelineError(
                f"Cannot open lock file {self.path}: {e} "
                f"(if the file is a symlink, that's a security concern — investigate)"
            ) from e
        self._fh = os.fdopen(fd, "w")
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._fh.close()
            self._fh = None
            raise PipelineError(f"Another pipeline run holds {self.path} — refusing to start")
        return self

    def __exit__(self, *exc):
        if self._fh is not None:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            finally:
                self._fh.close()
                self._fh = None


def load_pipeline_state() -> dict:
    data = load_json(PIPELINE_STATE_PATH, {"version": 1, "pipelines": {}})
    if not isinstance(data, dict) or "pipelines" not in data:
        data = {"version": 1, "pipelines": {}}
    return data


def save_pipeline_state(state: dict) -> None:
    atomic_write_json(PIPELINE_STATE_PATH, state)


def make_stage_record(status: str = "pending") -> dict:
    return {
        "status": status,
        "startedAt": None,
        "endedAt": None,
        "outputPath": None,
        "model": None,
        "durationSec": None,
        "stopReason": None,
        "error": None,
    }


def init_pipeline_record(task: dict, max_revisions: int = 2) -> dict:
    return {
        "taskId": task["id"],
        "startedAt": iso_now(),
        "endedAt": None,
        "status": "running",
        "currentStage": STAGES[0],
        "stages": {s: make_stage_record() for s in STAGES},
        "verificationCmd": task.get("verificationCmd", ""),
        "repoPath": task.get("repoPath") or task.get("repo_path") or "",
        "errors": [],
        # Revision loop tracking — see run_pipeline
        "maxRevisions": max_revisions,
        "revisions": {"planner": 0, "coder": 0},
        "revisionFeedback": {"planner": None, "coder": None},
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task loading + validation
# ──────────────────────────────────────────────────────────────────────────────

REQUIRED_TASK_FIELDS = ("id", "title", "verificationCmd")


def load_task(task_id: str) -> dict:
    data = load_json(TASKS_OPENCLAW)
    if data is None:
        raise TaskNotFound(f"{TASKS_OPENCLAW} does not exist")
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, dict) or task_id not in tasks:
        raise TaskNotFound(f"Task {task_id!r} not found in {TASKS_OPENCLAW}")
    task = tasks[task_id]
    missing = [f for f in REQUIRED_TASK_FIELDS if not task.get(f)]
    if missing:
        raise PipelineError(
            f"Task {task_id!r} missing required fields: {missing}. "
            f"See DISPATCH_TEMPLATE.md for required dispatch contract."
        )
    return task


# ──────────────────────────────────────────────────────────────────────────────
# Agent dispatch
# ──────────────────────────────────────────────────────────────────────────────


class AgentOutput:
    def __init__(self, text: str, raw: dict, duration_sec: float, stop_reason: str, model: str):
        self.text = text
        self.raw = raw
        self.duration_sec = duration_sec
        self.stop_reason = stop_reason
        self.model = model


def dispatch_agent(
    agent_id: str,
    message: str,
    timeout_sec: int,
    log_path: Path,
) -> AgentOutput:
    """Shell out to `openclaw agent --agent <id> --message <msg> --timeout <s> --json`.

    Writes raw JSON to log_path for forensics. Extracts finalAssistantVisibleText,
    stopReason, model via walk_for_key. Raises DispatchError on non-zero exit,
    timeout, or missing finalAssistantVisibleText.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = _dt.datetime.now()
    try:
        proc = subprocess.run(
            [
                "openclaw",
                "agent",
                "--agent", agent_id,
                "--message", message,
                "--timeout", str(timeout_sec),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_sec + 30,
        )
    except subprocess.TimeoutExpired as e:
        log_path.write_text(f"TIMEOUT after {timeout_sec}s\nstdout:\n{e.stdout or ''}\nstderr:\n{e.stderr or ''}")
        raise DispatchError(f"dispatch to {agent_id} timed out after {timeout_sec}s") from e

    log_path.write_text(proc.stdout + "\n--STDERR--\n" + proc.stderr)
    if proc.returncode != 0:
        raise DispatchError(
            f"openclaw agent --agent {agent_id} exited {proc.returncode}\n"
            f"stderr tail: {proc.stderr[-500:]}"
        )

    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DispatchError(f"dispatch to {agent_id} returned non-JSON: {proc.stdout[:500]}") from e

    text = walk_for_key(raw, "finalAssistantVisibleText")
    if not text:
        raise DispatchError(f"dispatch to {agent_id} had no finalAssistantVisibleText")
    stop_reason = walk_for_key(raw, "stopReason") or "unknown"
    model = walk_for_key(raw, "model") or "unknown"
    duration = (_dt.datetime.now() - start).total_seconds()
    return AgentOutput(str(text), raw, duration, str(stop_reason), str(model))


# ──────────────────────────────────────────────────────────────────────────────
# Stage implementations
# ──────────────────────────────────────────────────────────────────────────────


def outputs_dir_for(task_id: str) -> Path:
    p = OUTPUTS_DIR / task_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _start_stage(pstate: dict, name: str) -> dict:
    rec = pstate["stages"][name]
    rec["status"] = "running"
    rec["startedAt"] = iso_now()
    pstate["currentStage"] = name
    return rec


def _finish_stage(pstate: dict, name: str, *, output_path: str | None = None,
                  model: str | None = None, duration: float | None = None,
                  stop_reason: str | None = None, status: str = "completed") -> None:
    rec = pstate["stages"][name]
    rec["status"] = status
    rec["endedAt"] = iso_now()
    rec["outputPath"] = output_path
    rec["model"] = model
    rec["durationSec"] = duration
    rec["stopReason"] = stop_reason


def _fail_stage(pstate: dict, name: str, error: str) -> None:
    rec = pstate["stages"][name]
    rec["status"] = "failed"
    rec["endedAt"] = iso_now()
    rec["error"] = error
    pstate["errors"].append({"stage": name, "error": error, "at": iso_now()})


def stage_researcher(task: dict, pstate: dict) -> None:
    rec = _start_stage(pstate, "researcher")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})

    # External knowledge hook (Obsidian / autoresearch / any user-provided backend)
    external = load_external_context(task, "researcher")
    pstate["stages"]["researcher"]["externalContextBytes"] = len(external)
    external_block = ""
    if external:
        external_block = (
            "\n=== EXISTING KNOWLEDGE (from external context hook) ===\n"
            "The user has provided the following context from their knowledge base "
            "(Obsidian vault, autoresearch output, etc.). Build on this — don't repeat it. "
            "Your job is to add NOVEL findings via web research, citing sources. Explicitly "
            "note where your research confirms, contradicts, or extends the existing knowledge.\n"
            f"{external}\n"
            "=== END EXISTING KNOWLEDGE ===\n"
        )

    msg = (
        f"You are Oracle (Researcher). Produce a short research brief (≤10 bullets with "
        f"sources) for this task:\n\n"
        f"TASK: {task.get('title', '')}\n"
        f"OBJECTIVE: {task.get('objective') or task.get('summary', '')}\n"
        f"CONSTRAINTS: {task.get('constraints', 'none')}\n"
        f"{external_block}\n"
        f"Focus: latest best practices, known pitfalls, success factors, production gotchas. "
        f"Cite 2026-era sources where possible."
    )
    log = outputs_dir_for(task["id"]) / "00-researcher-raw.json"
    out = dispatch_agent("researcher", msg, DEFAULT_STAGE_TIMEOUT_SEC["researcher"], log)
    brief_path = outputs_dir_for(task["id"]) / "01-research-brief.md"
    brief_path.write_text(f"# Research Brief — {task['title']}\n\n{out.text}\n")
    _finish_stage(pstate, "researcher",
                  output_path=str(brief_path.relative_to(OPENCLAW_WORKSPACE)),
                  model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason)


def stage_planner(task: dict, pstate: dict) -> None:
    rec = _start_stage(pstate, "planner")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})
    brief_rel = pstate["stages"]["researcher"].get("outputPath")
    brief_text = ""
    if brief_rel:
        p = OPENCLAW_WORKSPACE / brief_rel
        if p.exists():
            brief_text = p.read_text()

    # Inject Librarian memory so past lessons shape the plan proactively.
    # See DELEGATION.md "Learn First" rule for Planner.
    librarian = load_librarian_memory()
    pstate["stages"]["planner"]["librarianBytes"] = len(librarian)

    # External knowledge hook (Obsidian / autoresearch / any user-provided backend)
    external = load_external_context(task, "planner")
    pstate["stages"]["planner"]["externalContextBytes"] = len(external)
    external_block = ""
    if external:
        external_block = (
            "=== EXTERNAL KNOWLEDGE BASE (from hook) ===\n"
            "The following domain knowledge comes from the user's external knowledge source "
            "(Obsidian vault, autoresearch output, etc.). Use it as authoritative context when "
            "drafting the plan. Cite the relevant pieces inline in the plan where they shape a "
            "decision, and include a '## External Knowledge Applied' section at the end listing "
            "how each piece informed the design.\n"
            f"{external}\n"
            "=== END EXTERNAL KNOWLEDGE BASE ===\n\n"
        )

    # If this is a revision attempt after Auditor REJECTED, prepend the feedback.
    revision_block = ""
    revision_feedback = pstate.get("revisionFeedback", {}).get("planner")
    revision_count = pstate.get("revisions", {}).get("planner", 0)
    if revision_feedback:
        revision_block = (
            f"⚠️  REVISION ATTEMPT {revision_count}/{pstate.get('maxRevisions', 2)} — "
            f"your prior plan was REJECTED by the adversarial Auditor.\n"
            f"You MUST address every gap below in the new draft. Do not re-submit the same plan.\n\n"
            f"=== AUDITOR REJECTION FEEDBACK ===\n{revision_feedback}\n"
            f"=== END REJECTION FEEDBACK ===\n\n"
        )

    msg = (
        revision_block +
        external_block +
        f"You are Architect (Planner, Opus 4.6). Draft a PLAN.md for this task. "
        f"Write it directly to {task.get('repoPath', '<repo>')}/PLAN.md.\n\n"
        "=== LIBRARIAN MEMORY — PAST LESSONS (read before drafting) ===\n"
        "Below are curated rules and lessons from past coding + debugging incidents.\n"
        "Every lesson that could apply to this task must be reflected in the plan as an\n"
        "explicit constraint, checkpoint, or verification step. Do not plan in a way that\n"
        "repeats past failures. Cite the relevant memory filename next to each checkpoint\n"
        "that was informed by a past lesson.\n"
        f"{librarian if librarian else '(no Librarian memory files found)'}\n"
        "=== END LIBRARIAN MEMORY ===\n\n"
        f"TASK: {task.get('title', '')}\n"
        f"OBJECTIVE: {task.get('objective') or task.get('summary', '')}\n"
        f"REPO: {task.get('repoPath', '')}\n"
        f"VERIFICATION COMMAND (Coder must make this pass): {task.get('verificationCmd', '')}\n\n"
        f"Follow DELEGATION.md 3-stage planning process. Embed the research brief below as "
        f"explicit checkpoints. Plan must include: file-by-file changes, test plan, edge cases, "
        f"and success criteria per the DISPATCH_TEMPLATE.md contract. Mark status as "
        f"'DRAFT — pending Grok 4.20 Beta adversarial review'. Include a 'Past Lessons Applied' "
        f"section listing every Librarian memory file you consulted and how it shaped the plan "
        f"(or 'not applicable' if it does not apply).\n\n"
        f"=== RESEARCH BRIEF ===\n{brief_text}"
    )
    log = outputs_dir_for(task["id"]) / "00-planner-raw.json"
    out = dispatch_agent("planner", msg, DEFAULT_STAGE_TIMEOUT_SEC["planner"], log)
    draft_path = outputs_dir_for(task["id"]) / "02-plan-draft.md"
    repo_plan = Path(task["repoPath"]) / "PLAN.md" if task.get("repoPath") else None
    if repo_plan and repo_plan.exists():
        draft_path.write_text(repo_plan.read_text())
    else:
        draft_path.write_text(out.text)
    _finish_stage(pstate, "planner",
                  output_path=str(draft_path.relative_to(OPENCLAW_WORKSPACE)),
                  model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason)
    # Post-review H4: clear revision feedback after successful consumption
    # so stale rejection text doesn't leak into later unrelated runs.
    if revision_feedback:
        pstate.setdefault("revisionFeedback", {})["planner"] = None


AUDITOR_REVIEW_START = "<!-- JARVIS_AUDITOR_REVIEW_START -->"
AUDITOR_REVIEW_END = "<!-- JARVIS_AUDITOR_REVIEW_END -->"


def _replace_or_append_auditor_review(target: Path, review_text: str) -> None:
    """Idempotently insert the Auditor review into a target file.

    Post-review M1 fix (2026-04-11): previous implementation used naive
    `open("a")` which caused duplicate review blocks to accumulate on
    `--resume` or revision loop re-runs. Now uses sentinel markers so
    re-running stage_auditor REPLACES the prior block in-place instead of
    appending.
    """
    block = (
        f"\n\n---\n\n{AUDITOR_REVIEW_START}\n"
        f"## Adversarial Review (Grok 4.20 Beta, {iso_now()})\n\n"
        f"{review_text}\n"
        f"{AUDITOR_REVIEW_END}\n"
    )
    try:
        existing = target.read_text()
    except OSError:
        existing = ""
    start_idx = existing.find(AUDITOR_REVIEW_START)
    end_idx = existing.find(AUDITOR_REVIEW_END)
    if start_idx >= 0 and end_idx > start_idx:
        # Replace in place. Trim the preceding "\n\n---\n\n" separator too
        # if it was inserted by a prior run.
        prefix_start = start_idx
        # Walk back over one leading "\n\n---\n\n" if present
        sep = "\n\n---\n\n"
        if prefix_start >= len(sep) and existing[prefix_start - len(sep): prefix_start] == sep:
            prefix_start -= len(sep)
        new_content = (
            existing[:prefix_start]
            + block
            + existing[end_idx + len(AUDITOR_REVIEW_END):]
        )
        target.write_text(new_content)
    else:
        target.write_text(existing + block)


def stage_auditor(task: dict, pstate: dict) -> None:
    rec = _start_stage(pstate, "auditor")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})
    draft_rel = pstate["stages"]["planner"].get("outputPath")
    if not draft_rel:
        raise PipelineError("Auditor: no planner output available")
    plan_text = (OPENCLAW_WORKSPACE / draft_rel).read_text()

    # Read Librarian memory so past lessons are enforced as part of review.
    # See DELEGATION.md "Learn Before Review" rule for Auditor.
    librarian = load_librarian_memory()
    pstate["stages"]["auditor"]["librarianBytes"] = len(librarian)

    msg = (
        "You are External Auditor (Grok 4.20 Beta). Stress-test this PLAN.md adversarially.\n\n"
        "=== LIBRARIAN MEMORY — PAST LESSONS (MANDATORY to apply) ===\n"
        "Below are curated rules and lessons from past coding + debugging incidents.\n"
        "Any plan that ignores a relevant lesson repeats the mistake. For every\n"
        "lesson that applies to this plan, either verify the plan handles it OR\n"
        "add a HIGH-severity gap citing the specific memory file.\n"
        f"{librarian if librarian else '(no Librarian memory files found)'}\n"
        "=== END LIBRARIAN MEMORY ===\n\n"
        "REVIEW CHECKLIST:\n"
        "1. Past-lesson enforcement — cite every Librarian memory above that applies.\n"
        "   Unaddressed lessons = HIGH severity gap. Applied lessons = note in 'Applied Lessons'.\n"
        "2. Missing edge cases\n"
        "3. Architectural weaknesses\n"
        "4. Production-readiness gaps ('what if X fails?')\n"
        "5. Launchd PATH bug class (plist must use /bin/zsh -lc OR EnvironmentVariables.PATH; "
        "see jarvis_launchd_path_bug.md)\n"
        "6. Atomic-write patterns for any state files\n"
        "7. Graceful degradation when inputs are missing\n"
        "8. Test coverage gaps\n\n"
        "Output format:\n"
        "### Gaps — numbered list, each with severity [HIGH/MED/LOW] and a concrete plan patch.\n"
        "   Prefix past-lesson gaps with the memory filename, e.g. "
        "'[HIGH] (jarvis_launchd_path_bug.md) — plist missing EnvironmentVariables.PATH'\n"
        "### Applied Lessons — list each Librarian memory you applied, one line each:\n"
        "   filename → how it informed the review (confirmed / gap added / not applicable)\n"
        "### Approval — 'APPROVED', 'APPROVED with patches', or 'REJECTED — needs revision'\n"
        "Under 1000 words.\n\n"
        f"=== PLAN.md ===\n{plan_text}"
    )
    log = outputs_dir_for(task["id"]) / "00-auditor-raw.json"
    out = dispatch_agent("auditor", msg, DEFAULT_STAGE_TIMEOUT_SEC["auditor"], log)

    # Replace or append the Auditor review (idempotent — see M1 fix)
    repo_plan = Path(task["repoPath"]) / "PLAN.md" if task.get("repoPath") else None
    target = repo_plan if repo_plan and repo_plan.exists() else OPENCLAW_WORKSPACE / draft_rel
    _replace_or_append_auditor_review(target, out.text)

    verdict = "REJECTED" if "REJECTED" in out.text.upper().split("APPROVAL")[-1][:300] else "APPROVED"
    pstate["stages"]["auditor"]["verdict"] = verdict
    pstate["stages"]["auditor"]["feedbackText"] = out.text  # preserved for revision loop
    merged_path = outputs_dir_for(task["id"]) / "03-plan-merged.md"
    merged_path.write_text(target.read_text())
    _finish_stage(pstate, "auditor",
                  output_path=str(merged_path.relative_to(OPENCLAW_WORKSPACE)),
                  model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason)
    if verdict == "REJECTED":
        raise AuditorRejected("Auditor returned REJECTED — pipeline must revise plan")


def _coder_host(task: dict) -> str:
    """Return the host the Coder stage should run on: 'local' or 'powerspec'.

    Controlled by `task["execution"]["coderHost"]`. Default is 'local' to
    preserve existing behavior — no existing tasks are affected.
    """
    exe = task.get("execution") or {}
    h = exe.get("coderHost") or "local"
    if h not in ("local", "powerspec"):
        raise PipelineError(f"invalid coderHost: {h!r}. Must be 'local' or 'powerspec'.")
    return h


def stage_coder(task: dict, pstate: dict) -> None:
    """Dispatch Coder locally or to PowerSpec based on task.execution.coderHost."""
    host = _coder_host(task)
    if host == "powerspec":
        return _dispatch_coder_powerspec(task, pstate)
    return _dispatch_coder_local(task, pstate)


def _dispatch_coder_local(task: dict, pstate: dict) -> None:
    rec = _start_stage(pstate, "coder")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})
    merged_rel = pstate["stages"]["auditor"].get("outputPath")
    plan_text = (OPENCLAW_WORKSPACE / merged_rel).read_text() if merged_rel else ""

    # Inject Librarian memory so past bugs don't get reintroduced in code.
    # See DELEGATION.md "Learn Before Code" rule for Coder.
    librarian = load_librarian_memory()
    pstate["stages"]["coder"]["librarianBytes"] = len(librarian)

    # If this is a revision attempt after Quality LLM REJECTED, prepend the feedback.
    revision_block = ""
    revision_feedback = pstate.get("revisionFeedback", {}).get("coder")
    revision_count = pstate.get("revisions", {}).get("coder", 0)
    if revision_feedback:
        revision_block = (
            f"⚠️  REVISION ATTEMPT {revision_count}/{pstate.get('maxRevisions', 2)} — "
            f"your prior commit was REJECTED by the Quality LLM review (tests passed but content failed).\n"
            f"You MUST address every reason below. Do not re-submit the same code.\n\n"
            f"=== QUALITY REJECTION FEEDBACK ===\n{revision_feedback}\n"
            f"=== END REJECTION FEEDBACK ===\n\n"
        )

    msg = (
        revision_block +
        f"You are Scotty (Coder, Opus 4.6). Implement the following PLAN.md. "
        f"The plan has been adversarially reviewed by Grok 4.20 Beta — APPLY all Auditor patches "
        f"as part of implementation.\n\n"
        "=== LIBRARIAN MEMORY — PAST LESSONS (read before coding) ===\n"
        "Below are curated rules and lessons from past coding + debugging incidents.\n"
        "Apply each relevant lesson as a code-level constraint. Do NOT reintroduce any past bug.\n"
        "Examples of how to apply:\n"
        "  - If a memory says 'launchd plists using /usr/bin/env need EnvironmentVariables.PATH',\n"
        "    any plist you write must include that block.\n"
        "  - If a memory says 'always atomic-write JSON via tmp + os.replace', do that.\n"
        "  - If a memory names a failure mode (e.g. 'gog gmail search is scope-restricted after\n"
        "    2026-04-11'), don't use that code path.\n"
        "If a PLAN.md instruction conflicts with a past lesson, follow the past lesson and flag\n"
        "the conflict in your final summary — the plan may be wrong.\n"
        f"{librarian if librarian else '(no Librarian memory files found)'}\n"
        "=== END LIBRARIAN MEMORY ===\n\n"
        f"REPO: {task.get('repoPath', '')}\n"
        f"VERIFICATION COMMAND (must pass before you commit): {task.get('verificationCmd', '')}\n\n"
        f"Rules:\n"
        f"- Run the verification command before committing\n"
        f"- Single git commit on master with a clear message referencing the task id {task['id']}\n"
        f"- Return a structured summary: files changed, lines +/-, test count before/after, commit SHA, "
        f"and a 'Past Lessons Applied' section listing each Librarian memory you consulted and how it "
        f"shaped the implementation (or 'not applicable' if it does not apply)\n\n"
        f"=== PLAN.md (merged with Auditor patches) ===\n{plan_text}"
    )
    log = outputs_dir_for(task["id"]) / "00-coder-raw.json"
    out = dispatch_agent("coder", msg, DEFAULT_STAGE_TIMEOUT_SEC["coder"], log)
    summary_path = outputs_dir_for(task["id"]) / "04-coder-summary.md"
    summary_path.write_text(out.text)
    # Capture commit SHA
    sha = ""
    if task.get("repoPath"):
        try:
            r = subprocess.run(
                ["git", "-C", task["repoPath"], "log", "-1", "--format=%H"],
                capture_output=True, text=True, check=True,
            )
            sha = r.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    pstate["stages"]["coder"]["commitSha"] = sha
    _finish_stage(pstate, "coder",
                  output_path=str(summary_path.relative_to(OPENCLAW_WORKSPACE)),
                  model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason)
    # Post-review H4: clear revision feedback after successful consumption
    if revision_feedback:
        pstate.setdefault("revisionFeedback", {})["coder"] = None


def _powerspec_remote_work_dir(task: dict) -> str:
    """Return the Windows path for this task's work dir on PowerSpec."""
    exe = task.get("execution") or {}
    explicit = exe.get("remoteWorkDir")
    if explicit:
        return explicit
    return rf"{POWERSPEC_REMOTE_BASE_DIR}\{task['id']}"


def _dispatch_coder_powerspec(task: dict, pstate: dict) -> None:
    """Dispatch Coder to PowerSpec via the Mac's main agent + exec tool.

    Architecture (proven in Phase 0 spike, 2026-04-11):
      orchestrator → openclaw agent --agent main → exec tool with host=PowerSpec
      → PowerSpec node host → `cmd /c "echo <prompt> | claude.cmd --print --dangerously-skip-permissions"`

    The `cmd /c echo | claude.cmd` invocation pattern is required because
    claude.cmd on Windows drops positional-prompt argv when called directly
    via non-TTY subprocess. stdin piping works reliably.

    Git operations (clone/commit/push) happen ON PowerSpec in the remote work
    dir. Commit SHA is captured via a second exec call to `git log -1`.
    Librarian memory is passed through the prompt. MC is updated with
    host=powerspec in the agentChain.
    """
    rec = _start_stage(pstate, "coder")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})

    merged_rel = pstate["stages"]["auditor"].get("outputPath")
    plan_text = (OPENCLAW_WORKSPACE / merged_rel).read_text() if merged_rel else ""
    librarian = load_librarian_memory()
    pstate["stages"]["coder"]["librarianBytes"] = len(librarian)
    pstate["stages"]["coder"]["host"] = "powerspec"  # recorded for MC + audit

    # Revision feedback (same logic as local dispatch)
    revision_block = ""
    revision_feedback = pstate.get("revisionFeedback", {}).get("coder")
    revision_count = pstate.get("revisions", {}).get("coder", 0)
    if revision_feedback:
        revision_block = (
            f"⚠️  REVISION ATTEMPT {revision_count}/{pstate.get('maxRevisions', 2)} — "
            f"your prior commit was REJECTED by Quality. Address every reason below.\n"
            f"=== QUALITY REJECTION FEEDBACK ===\n{revision_feedback}\n"
            f"=== END ===\n\n"
        )

    work_dir = _powerspec_remote_work_dir(task)

    # Build the task description that Claude Code on PowerSpec will execute.
    # Note: Librarian memory is injected as part of the prompt content, not
    # via a separate mechanism — Claude Code on PowerSpec sees it inline.
    coder_prompt = (
        revision_block +
        f"You are Coder (Claude Code on PowerSpec). Implement the task per PLAN.md. "
        f"Working dir: {work_dir}. After implementation, git add/commit/push to origin. "
        f"Single commit referencing task id {task['id']}. "
        f"Return a structured summary: files changed, lines +/-, tests before/after, commit SHA. "
        f"Apply these past lessons from Librarian memory (do not reintroduce any documented bug):\n"
        f"{librarian}\n\n"
        f"=== PLAN.md (merged with Auditor patches) ===\n{plan_text}"
    )

    # Verify node is alive (auto-restart if idle-disconnected)
    _powerspec_ensure_node_alive()

    # Plumbing: ensure work dir, stage prompt file via SSH
    _powerspec_ensure_work_dir(task, work_dir)
    _powerspec_stage_prompt(task, work_dir, coder_prompt)

    # Workload: dispatch the actual Claude Code run via the Mac's main agent +
    # exec tool with host=PowerSpec. This is the Option C path that matters.
    #
    # Fix for KNOWN_FAILURES.md "exec stdout pipe hang": the main agent's exec
    # tool call may hang after Claude Code finishes because cmd.exe keeps the
    # stdout pipe open. We use an optimistic-timeout pattern: set a moderate
    # outer timeout (~10 min), and if it expires, check whether _output.txt on
    # PowerSpec has content. If yes, Claude Code finished and the hang is benign
    # — we recover by reading the file directly via SSH.
    dispatch_msg = _build_powerspec_dispatch_message(work_dir)
    log = outputs_dir_for(task["id"]) / "00-coder-raw.json"
    optimistic_timeout = min(POWERSPEC_EXEC_TIMEOUT_SEC, 600)  # cap at 10 min
    pipe_hung = False
    try:
        out = dispatch_agent(
            "main", dispatch_msg,
            optimistic_timeout + 60,  # slight buffer
            log,
        )
    except DispatchError as e:
        # Check if Claude Code actually finished despite the pipe hang
        _mc_log(f"Coder dispatch timed out at {optimistic_timeout}s — checking for output on PowerSpec")
        remote_check = _powerspec_read_output(work_dir)
        if remote_check and len(remote_check) > 50:
            _mc_log(f"Output present ({len(remote_check)} bytes) — recovering from pipe hang")
            out = AgentOutput(
                text=f"[pipe-hang recovery] Output captured via SSH ({len(remote_check)} bytes)",
                raw={}, duration_sec=float(optimistic_timeout),
                stop_reason="timeout-recovered", model="recovered-via-ssh",
            )
            pipe_hung = True
        else:
            raise  # truly failed — no output exists

    # Read the full Claude Code output from PowerSpec (SSH plumbing)
    remote_output = _powerspec_read_output(work_dir)
    if pipe_hung:
        _mc_log(f"Pipe-hang recovery: using SSH-read output ({len(remote_output)} bytes)")
    summary_path = outputs_dir_for(task["id"]) / "04-coder-summary.md"
    summary_path.write_text(
        f"# Coder output (from PowerSpec)\n\n"
        f"## Dispatch status (main agent reply)\n{out.text}\n\n"
        f"## Claude Code output (captured from _output.txt on PowerSpec)\n{remote_output}\n"
    )

    # Capture commit SHA from PowerSpec's remote git repo
    sha = _powerspec_capture_commit_sha(task, work_dir)
    pstate["stages"]["coder"]["commitSha"] = sha
    _finish_stage(
        pstate, "coder",
        output_path=str(summary_path.relative_to(OPENCLAW_WORKSPACE)),
        model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason,
    )
    # Clear revision feedback after successful consumption
    if revision_feedback:
        pstate.setdefault("revisionFeedback", {})["coder"] = None


def _powerspec_ensure_node_alive() -> None:
    """Verify the PowerSpec node is connected to the Mac gateway. If not, restart it.

    Fix for KNOWN_FAILURES.md "PowerSpec openclaw node host disconnects after ~50 min idle".
    Called at the top of `_dispatch_coder_powerspec()` before any real work starts.
    """
    # Quick check: `openclaw nodes list` output includes "just now" or recent timestamp
    # when the node is connected. If not, restart.
    try:
        proc = subprocess.run(
            ["openclaw", "nodes", "list", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        import json as _json
        if proc.returncode == 0:
            try:
                data = _json.loads(proc.stdout)
                paired = data.get("paired") or []
                for node in paired:
                    if isinstance(node, dict) and node.get("displayName") == POWERSPEC_NODE_NAME:
                        # Node is in the paired list — but is it connected?
                        # The JSON output may include a `connected` or `lastConnectMs` field.
                        # If connected, we're good. If we can't tell, probe via exec.
                        break
            except (_json.JSONDecodeError, KeyError, TypeError):
                pass  # can't parse, fall through to probe
    except (subprocess.SubprocessError, OSError):
        pass

    # Probe: try a trivial exec call. If it works, node is alive.
    try:
        probe = subprocess.run(
            [
                "openclaw", "agent", "--agent", "main",
                "--message", f"Use the exec tool with host={POWERSPEC_NODE_NAME} and invokeTimeout=15000. "
                              'Run this argv: ["cmd", "/c", "echo alive"]. Return only stdout.',
                "--timeout", "30",
                "--json",
            ],
            capture_output=True, text=True, timeout=45,
        )
        if proc.returncode == 0 and "alive" in (probe.stdout or ""):
            return  # node is alive
    except (subprocess.SubprocessError, OSError):
        pass

    # Node appears dead. Restart via SSH.
    _mc_log("PowerSpec node not connected — restarting via SSH")
    try:
        _powerspec_ssh('schtasks /end /tn "OpenClaw Node"', timeout=15)
        import time
        time.sleep(2)
        _powerspec_ssh(
            'powershell -Command "Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force"',
            timeout=15,
        )
        time.sleep(1)
        _powerspec_ssh('schtasks /run /tn "OpenClaw Node"', timeout=15)
        time.sleep(5)
        _mc_log("PowerSpec node restarted via SSH — waiting for reconnection")
    except (subprocess.SubprocessError, OSError) as e:
        raise PipelineError(f"Cannot restart PowerSpec node host: {e}") from e


def _powerspec_ensure_work_dir(task: dict, work_dir: str) -> None:
    """Ensure the remote work dir exists on PowerSpec. SSH-based (plumbing).

    If `task.execution.remoteGitRepo` is set and the dir doesn't exist, clones
    that URL. Otherwise creates dir + git init if empty.

    Note: paths with spaces (like "Eric Brown") are single-quoted inside the
    PowerShell command string so they survive the shell-inside-shell nesting.
    """
    exe = task.get("execution") or {}
    remote_repo = exe.get("remoteGitRepo")
    # Use single quotes for paths inside PowerShell — they're literal in PS and
    # don't conflict with the outer double-quoted bash string.
    ps = (
        f"New-Item -ItemType Directory -Path '{POWERSPEC_REMOTE_BASE_DIR}' -Force | Out-Null; "
        f"if (!(Test-Path '{work_dir}')) {{ "
    )
    if remote_repo:
        ps += f"git clone {remote_repo} '{work_dir}' "
    else:
        ps += f"New-Item -ItemType Directory -Path '{work_dir}' | Out-Null; Set-Location '{work_dir}'; git init -q "
    ps += "}"
    proc = _powerspec_ssh(f'powershell -Command "{ps}"', timeout=120)
    if proc.returncode != 0:
        raise PipelineError(f"PowerSpec work dir setup failed: {proc.stderr[:300]}")


def _powerspec_stage_prompt(task: dict, work_dir: str, prompt_text: str) -> None:
    """Write the coder prompt to <work_dir>\\_prompt.txt on PowerSpec via SSH+scp."""
    import tempfile as _tempfile
    # Write prompt to a local temp file, scp to PowerSpec
    with _tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt_text)
        local_path = f.name
    try:
        # Use scp with the same User pattern as SSH (no spaces in scp username parsing bug workaround)
        remote_dest = f"{work_dir}\\_prompt.txt".replace("\\", "/")
        proc = subprocess.run(
            [
                "scp",
                "-o", f'User="{POWERSPEC_SSH_USER}"',
                "-o", "StrictHostKeyChecking=accept-new",
                local_path,
                f"{POWERSPEC_SSH_ADDR}:{remote_dest}",
            ],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            raise PipelineError(f"scp prompt to PowerSpec failed: {proc.stderr[:300]}")
    finally:
        try:
            os.unlink(local_path)
        except OSError:
            pass


def _powerspec_read_output(work_dir: str) -> str:
    """Read _output.txt from PowerSpec work dir via SSH."""
    ps = f"Get-Content '{work_dir}\\_output.txt' -Raw -ErrorAction SilentlyContinue"
    proc = _powerspec_ssh(f'powershell -Command "{ps}"', timeout=60)
    return (proc.stdout or "").strip()


def _powerspec_capture_commit_sha(task: dict, work_dir: str) -> str:
    """Read git HEAD sha from PowerSpec's remote work dir via SSH."""
    ps = f"Set-Location '{work_dir}'; git log -1 --format=%H 2>$null"
    try:
        proc = _powerspec_ssh(f'powershell -Command "{ps}"', timeout=60)
        sha = (proc.stdout or "").strip()
        if len(sha) >= 40:
            return sha
    except (subprocess.SubprocessError, OSError):
        pass
    return ""


def _build_powerspec_dispatch_message(work_dir: str) -> str:
    """Build a SHORT, unambiguous instruction for the Mac's main agent.

    The prompt file is already staged on PowerSpec at <work_dir>\\_prompt.txt
    (via SSH/scp plumbing). Main just needs to make ONE exec tool call via
    the openclaw nodes exec path to run claude.cmd against that prompt.
    """
    # Single cmd /c command — short, no nested quoting hell
    shell_cmd = (
        f'cd /d "{work_dir}" && '
        f'type _prompt.txt | {POWERSPEC_CLAUDE_CMD} --print --dangerously-skip-permissions --model sonnet > _output.txt 2>&1 && '
        f'echo CODER_RUN_COMPLETE'
    )
    return (
        f"Use the exec tool. Set host={POWERSPEC_NODE_NAME} and invokeTimeout={POWERSPEC_EXEC_TIMEOUT_SEC * 1000}.\n"
        f"Run this exact 3-element argv:\n"
        f'  ["cmd", "/c", {shell_cmd!r}]\n\n'
        f"Return only the captured stdout. If you see 'CODER_RUN_COMPLETE' at the end, "
        f"the run succeeded (the full Claude Code output is in _output.txt on PowerSpec — "
        f"the orchestrator will read it separately)."
    )


def stage_quality(task: dict, pstate: dict) -> None:
    """Hybrid gate: (1) run verificationCmd deterministically, (2) ask Quality (Grok) to judge output.

    Security: `verificationCmd` accepts EITHER a string (legacy, runs under
    `shell=True` — only safe when tasks.json is fully trusted) OR a list of
    argv (preferred — runs without a shell, immune to command injection).
    See post-review H1 fix 2026-04-11.
    """
    rec = _start_stage(pstate, "quality")
    save_pipeline_state({"version": 1, "pipelines": {task["id"]: pstate}})
    cmd = task.get("verificationCmd", "")
    # For local Coder tasks, cwd = task.repoPath (Mac-local dir).
    # For PowerSpec Coder tasks, repoPath is a Windows path that doesn't exist on
    # the Mac, so we fall back to the user's home dir for the subprocess cwd.
    # The verificationCmd itself is responsible for SSH-ing to PowerSpec to check.
    exe = task.get("execution") or {}
    if exe.get("coderHost") == "powerspec":
        repo = str(Path.home())
    else:
        repo = task.get("repoPath") or str(Path.home())
        if not Path(repo).exists():
            repo = str(Path.home())  # safety fallback
    cmd_log = outputs_dir_for(task["id"]) / "05-quality-cmd.log"

    # Step 1: deterministic verification — dispatch by type to avoid shell injection
    # when callers provide argv-list form.
    if isinstance(cmd, list):
        shell_mode = "argv"
        proc = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, timeout=600,
        )
    elif isinstance(cmd, str) and cmd:
        shell_mode = "shell-string"
        proc = subprocess.run(
            cmd, shell=True, cwd=repo, capture_output=True, text=True, timeout=600,
        )
    else:
        # Reject empty or wrong-type verificationCmd loudly instead of silently passing
        raise QualityGateFailed(
            f"verificationCmd must be a non-empty string or list (got {type(cmd).__name__})"
        )
    pstate["stages"]["quality"]["shellMode"] = shell_mode
    cmd_log.write_text(
        f"cmd: {cmd!r}\nshell_mode: {shell_mode}\ncwd: {repo}\nexit: {proc.returncode}\n"
        f"--stdout--\n{proc.stdout}\n--stderr--\n{proc.stderr}\n"
    )
    pstate["stages"]["quality"]["cmdExit"] = proc.returncode
    if proc.returncode != 0:
        _fail_stage(pstate, "quality", f"verificationCmd exited {proc.returncode}")
        raise QualityGateFailed(f"verificationCmd failed (exit {proc.returncode}); see {cmd_log}")

    # Step 2: LLM content review via Quality agent (now Grok 4.20 Beta)
    sha = pstate["stages"]["coder"].get("commitSha", "")
    diffstat = ""
    if sha and repo:
        try:
            r = subprocess.run(
                ["git", "-C", repo, "show", "--stat", sha],
                capture_output=True, text=True, check=True,
            )
            diffstat = r.stdout
        except subprocess.CalledProcessError:
            pass
    msg = (
        "You are Inspector (Quality, Grok 4.20 Beta). The verification command PASSED — "
        "your job is to judge whether the OUTPUT is CORRECT, not just whether exit was 0. "
        "Catch 'tests pass but requirement skipped' issues.\n\n"
        f"TASK: {task.get('title', '')}\n"
        f"OBJECTIVE: {task.get('objective') or task.get('summary', '')}\n"
        f"SUCCESS CRITERIA: {task.get('success_criteria', 'see objective')}\n"
        f"FAILURE CRITERIA: {task.get('failure_criteria', 'none')}\n\n"
        f"Commit SHA: {sha}\n"
        f"--- git show --stat ---\n{diffstat}\n"
        f"--- verificationCmd stdout tail (last 2000 chars) ---\n{proc.stdout[-2000:]}\n\n"
        "Verdict format:\n"
        "### Verdict — APPROVED or REJECTED\n"
        "### Reasons — numbered list\n"
        "Under 400 words."
    )
    log = outputs_dir_for(task["id"]) / "00-quality-raw.json"
    out = dispatch_agent("quality", msg, DEFAULT_STAGE_TIMEOUT_SEC["quality"], log)
    verdict_path = outputs_dir_for(task["id"]) / "06-quality-verdict.md"
    verdict_path.write_text(out.text)
    verdict = "REJECTED" if "REJECTED" in out.text.upper().split("VERDICT")[-1][:200] else "APPROVED"
    pstate["stages"]["quality"]["verdict"] = verdict
    pstate["stages"]["quality"]["feedbackText"] = out.text  # preserved for revision loop
    _finish_stage(pstate, "quality",
                  output_path=str(verdict_path.relative_to(OPENCLAW_WORKSPACE)),
                  model=out.model, duration=out.duration_sec, stop_reason=out.stop_reason)
    if verdict == "REJECTED":
        _fail_stage(pstate, "quality", "Quality LLM returned REJECTED despite cmd pass")
        raise QualityGateFailed("Quality LLM REJECTED — see verdict file")


def step_monitor(task: dict, pstate: dict) -> None:
    _start_stage(pstate, "monitor")
    # Log incident only if any prior stage failed
    failed = [s for s in STAGES if pstate["stages"][s].get("status") == "failed"]
    if failed:
        INCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        incident = {
            "timestamp": iso_now(),
            "agent": "jarvis-pipeline",
            "project": task.get("id", "unknown"),
            "error_category": "pipeline",
            "error_summary": f"Pipeline halted at stage(s) {failed}",
            "root_cause": "see pipeline-state.json",
            "fix_applied": "none — pipeline halted",
            "prevention": "downstream review",
            "resolved": False,
        }
        with open(INCIDENTS_PATH, "a") as f:
            f.write(json.dumps(incident) + "\n")
    _finish_stage(pstate, "monitor", status="completed")


def _update_task_stores(task: dict, pstate: dict) -> None:
    """Dual-write Conductor-style to both tasks.json stores."""
    task_id = task["id"]
    overall_ok = all(pstate["stages"][s]["status"] == "completed" for s in STAGES)
    status = "completed" if overall_ok else "failed"
    progress = 100 if overall_ok else 0
    sha = pstate["stages"]["coder"].get("commitSha", "")

    # Dict-form stores (openclaw-workspace + .openclaw/workspace mirror)
    for p in (TASKS_OPENCLAW, TASKS_OPENCLAW_MIRROR):
        if not p.exists():
            continue
        d = load_json(p)
        if isinstance(d, dict) and isinstance(d.get("tasks"), dict) and task_id in d["tasks"]:
            t = d["tasks"][task_id]
            t["status"] = status
            t["progress"] = progress
            t["completedAt"] = iso_now() if overall_ok else None
            if sha:
                t["completedCommit"] = sha
            t["lastUpdate"] = f"jarvis-pipeline {status}"
            atomic_write_json(p, d)

    # Array-form store (Mission Control) — optional
    if TASKS_MISSION_CONTROL.exists():
        d = load_json(TASKS_MISSION_CONTROL)
        updated = False
        if isinstance(d, list):
            for t in d:
                if isinstance(t, dict) and t.get("id") == task_id:
                    t["status"] = status
                    t["progress"] = progress
                    t["completedAt"] = iso_now() if overall_ok else None
                    if sha:
                        t["completedCommit"] = sha
                    t.setdefault("updates", []).append({
                        "timestamp": iso_now(),
                        "text": f"jarvis-pipeline {status}"
                    })
                    updated = True
                    break
        elif isinstance(d, dict) and isinstance(d.get("tasks"), dict):
            t = d["tasks"].get(task_id)
            if t:
                t["status"] = status
                t["progress"] = progress
                t["completedAt"] = iso_now() if overall_ok else None
                if sha:
                    t["completedCommit"] = sha
                updated = True
        if updated:
            atomic_write_json(TASKS_MISSION_CONTROL, d)


def step_conductor(task: dict, pstate: dict) -> None:
    _start_stage(pstate, "conductor")
    # Mark conductor complete BEFORE the dual-write so that `overall_ok`
    # in _update_task_stores sees every stage as completed.
    _finish_stage(pstate, "conductor", status="completed")
    _update_task_stores(task, pstate)


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────


STAGE_FUNCS = {
    "researcher": stage_researcher,
    "planner": stage_planner,
    "auditor": stage_auditor,
    "coder": stage_coder,
    "quality": stage_quality,
    "monitor": step_monitor,
    "conductor": step_conductor,
}


def run_pipeline(task_id: str, resume: bool, skip_stages: set[str], max_revisions: int = 2) -> dict:
    """Run the 7-stage pipeline end-to-end.

    Supports two kinds of revision loops (bounded by `max_revisions`):
      - Auditor REJECTED → re-run Planner with Auditor's feedback, then Auditor again
      - Quality LLM REJECTED (cmd passed) → re-run Coder with Quality's feedback, then Quality again

    A deterministic verificationCmd failure in Quality does NOT trigger a retry —
    it halts the pipeline. Same for any non-rejection PipelineError.
    """
    task = load_task(task_id)
    with StateLock(PIPELINE_LOCK_PATH):
        state = load_pipeline_state()
        pstate = state["pipelines"].get(task_id)
        if pstate is None or not resume:
            pstate = init_pipeline_record(task, max_revisions=max_revisions)
            state["pipelines"][task_id] = pstate
            save_pipeline_state(state)
        else:
            # Ensure older state records have the revision fields
            pstate.setdefault("maxRevisions", max_revisions)
            pstate.setdefault("revisions", {"planner": 0, "coder": 0})
            pstate.setdefault("revisionFeedback", {"planner": None, "coder": None})

        # Mission Control: ensure the task is registered and marked running
        _mc_ensure_task(task)

        idx = 0
        while idx < len(STAGES):
            name = STAGES[idx]
            if name in skip_stages:
                _mc_update_stage(task, name, "skipped")
                idx += 1
                continue
            rec = pstate["stages"][name]
            if rec["status"] == "completed":
                print(f"[{name}] ✓ already completed — skipping")
                _mc_update_stage(task, name, "skipped")
                idx += 1
                continue
            print(f"[{name}] ▶ running…")
            _mc_update_stage(task, name, "start")
            try:
                STAGE_FUNCS[name](task, pstate)
                state["pipelines"][task_id] = pstate
                save_pipeline_state(state)
                print(f"[{name}] ✓ done ({rec.get('durationSec') or '?'}s, {rec.get('model') or 'local'})")
                extra = None
                if name == "coder" and pstate["stages"]["coder"].get("commitSha"):
                    extra = {"completedCommit": pstate["stages"]["coder"]["commitSha"]}
                _mc_update_stage(task, name, "done", extra=extra)
                idx += 1
            except AuditorRejected as e:
                # Revision loop: re-run Planner with Auditor's feedback.
                # Post-review H4 fix (2026-04-11): also preserve the feedback
                # text BEFORE resetting the auditor stage record, and clear
                # the revision feedback after successful consumption.
                feedback_text = pstate["stages"]["auditor"].get("feedbackText", str(e))
                rev_count = pstate["revisions"]["planner"]
                if rev_count < pstate["maxRevisions"]:
                    pstate["revisions"]["planner"] = rev_count + 1
                    pstate["revisionFeedback"]["planner"] = feedback_text
                    # Reset Planner and Auditor to pending. Using `make_stage_record()`
                    # ensures NO leftover fields (outputPath, verdict, feedbackText, etc.)
                    # from the rejected attempt — prevents mixed 'failed-but-has-completed-data'.
                    pstate["stages"]["planner"] = make_stage_record()
                    pstate["stages"]["auditor"] = make_stage_record()
                    pstate["currentStage"] = "planner"
                    state["pipelines"][task_id] = pstate
                    save_pipeline_state(state)
                    print(f"[auditor] ⟳ REJECTED → revising plan (attempt {rev_count + 1}/{pstate['maxRevisions']})")
                    _mc_update_stage(task, "planner", "revising")
                    # Post-review M6: brief backoff before retry so we don't
                    # hammer the provider on repeated rejections.
                    import time
                    time.sleep(min(2 ** rev_count, 10))
                    idx = STAGES.index("planner")
                    continue
                else:
                    # Revisions exhausted. Clean up state: start from a fresh
                    # stage record so _fail_stage's fields are the only ones present.
                    pstate["stages"]["auditor"] = make_stage_record()
                    _fail_stage(pstate, "auditor", f"REJECTED after {pstate['maxRevisions']} revisions: {e}")
                    pstate["status"] = "failed"
                    pstate["endedAt"] = iso_now()
                    state["pipelines"][task_id] = pstate
                    save_pipeline_state(state)
                    print(f"[auditor] ✗ FAILED: revisions exhausted ({pstate['maxRevisions']}/{pstate['maxRevisions']})")
                    _mc_update_stage(task, "auditor", "failed")
                    _mc_finalize(task, pstate)
                    try:
                        step_monitor(task, pstate)
                        save_pipeline_state(state)
                    except (OSError, ValueError):
                        pass
                    return pstate
            except QualityGateFailed as e:
                # Revision loop: re-run Coder ONLY if cmd passed (LLM rejection),
                # NOT if verificationCmd itself failed (that's a hard halt).
                # Post-review H4 + M6 fix (2026-04-11).
                cmd_exit = pstate["stages"]["quality"].get("cmdExit", 1)
                feedback_text = pstate["stages"]["quality"].get("feedbackText", str(e))
                rev_count = pstate["revisions"]["coder"]
                if cmd_exit == 0 and rev_count < pstate["maxRevisions"]:
                    pstate["revisions"]["coder"] = rev_count + 1
                    pstate["revisionFeedback"]["coder"] = feedback_text
                    pstate["stages"]["coder"] = make_stage_record()
                    pstate["stages"]["quality"] = make_stage_record()
                    pstate["currentStage"] = "coder"
                    state["pipelines"][task_id] = pstate
                    save_pipeline_state(state)
                    print(f"[quality] ⟳ LLM REJECTED → revising code (attempt {rev_count + 1}/{pstate['maxRevisions']})")
                    _mc_update_stage(task, "coder", "revising")
                    import time
                    time.sleep(min(2 ** rev_count, 10))
                    idx = STAGES.index("coder")
                    continue
                else:
                    pstate["stages"]["quality"] = make_stage_record()
                    _fail_stage(pstate, "quality", str(e))
                    pstate["status"] = "failed"
                    pstate["endedAt"] = iso_now()
                    state["pipelines"][task_id] = pstate
                    save_pipeline_state(state)
                    reason = "cmd failed" if cmd_exit != 0 else f"revisions exhausted ({pstate['maxRevisions']}/{pstate['maxRevisions']})"
                    print(f"[quality] ✗ FAILED: {e} ({reason})")
                    _mc_update_stage(task, "quality", "failed")
                    _mc_finalize(task, pstate)
                    try:
                        step_monitor(task, pstate)
                        save_pipeline_state(state)
                    except (OSError, ValueError):
                        pass
                    return pstate
            except PipelineError as e:
                _fail_stage(pstate, name, str(e))
                pstate["status"] = "failed"
                pstate["endedAt"] = iso_now()
                state["pipelines"][task_id] = pstate
                save_pipeline_state(state)
                print(f"[{name}] ✗ FAILED: {e}")
                _mc_update_stage(task, name, "failed")
                _mc_finalize(task, pstate)
                if name != "monitor":
                    try:
                        step_monitor(task, pstate)
                        state["pipelines"][task_id] = pstate
                        save_pipeline_state(state)
                    except (OSError, ValueError):
                        pass  # post-review H2: narrowed from Exception
                return pstate
        pstate["status"] = "completed"
        pstate["endedAt"] = iso_now()
        state["pipelines"][task_id] = pstate
        save_pipeline_state(state)
        _mc_finalize(task, pstate)
    return pstate


def format_report(pstate: dict) -> str:
    lines = [
        f"Pipeline {pstate['taskId']} — {pstate['status']}",
        f"  started: {pstate['startedAt']}  ended: {pstate.get('endedAt') or '-'}",
    ]
    revs = pstate.get("revisions") or {}
    if revs.get("planner") or revs.get("coder"):
        lines.append(f"  revisions: planner={revs.get('planner',0)}  coder={revs.get('coder',0)}  max={pstate.get('maxRevisions','?')}")
    lines.append("")
    for name in STAGES:
        rec = pstate["stages"][name]
        mark = {"completed": "✓", "running": "…", "pending": " ", "failed": "✗"}.get(rec["status"], "?")
        dur = f"{rec.get('durationSec') or 0:.0f}s" if rec.get("durationSec") else "-"
        model = rec.get("model") or "local"
        extra = ""
        if rec.get("verdict"):
            extra = f" verdict={rec['verdict']}"
        if rec.get("error"):
            extra = f" error={rec['error'][:60]}"
        lines.append(f"  {mark} {name:12} {rec['status']:10} {dur:>6}  {model}{extra}")
    if pstate.get("errors"):
        lines.append("")
        lines.append("Errors:")
        for e in pstate["errors"]:
            lines.append(f"  - [{e['stage']}] {e['error']}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def cmd_run(args):
    skip = set(args.skip_stage or [])
    pstate = run_pipeline(args.task_id, args.resume, skip, max_revisions=args.max_revision_loops)
    print("\n" + format_report(pstate))
    return 0 if pstate["status"] == "completed" else 1


def cmd_status(args):
    state = load_pipeline_state()
    pstate = state["pipelines"].get(args.task_id)
    if pstate is None:
        print(f"No pipeline state for task {args.task_id!r}")
        return 2
    print(format_report(pstate))
    return 0


def cmd_reset(args):
    with StateLock(PIPELINE_LOCK_PATH):
        state = load_pipeline_state()
        if args.task_id not in state["pipelines"]:
            print(f"No pipeline state for task {args.task_id!r}")
            return 2
        del state["pipelines"][args.task_id]
        save_pipeline_state(state)
    print(f"Reset pipeline state for {args.task_id}")
    return 0


def cmd_list(args):
    state = load_pipeline_state()
    if not state["pipelines"]:
        print("(no pipelines tracked)")
        return 0
    for tid, p in state["pipelines"].items():
        cur = p.get("currentStage", "?")
        print(f"{tid:40} {p['status']:12} current={cur:12} started={p['startedAt']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="jarvis-pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Run a pipeline")
    r.add_argument("task_id")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--skip-stage", action="append", help="skip stage (repeatable)")
    r.add_argument("--max-revision-loops", type=int, default=2,
                   help="max Auditor-REJECT→Planner-revise and Quality-REJECT→Coder-revise attempts (default: 2)")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("status", help="Show pipeline state")
    s.add_argument("task_id")
    s.set_defaults(func=cmd_status)

    res = sub.add_parser("reset", help="Wipe pipeline state for a task")
    res.add_argument("task_id")
    res.set_defaults(func=cmd_reset)

    ls = sub.add_parser("list", help="List all tracked pipelines")
    ls.set_defaults(func=cmd_list)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
