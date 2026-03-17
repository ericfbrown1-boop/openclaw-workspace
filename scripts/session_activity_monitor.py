#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path

LOG_DIR = Path.home() / '.openclaw' / 'workspace' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'session_activity_monitor.log'
THRESHOLD_MS = 12 * 60 * 60 * 1000  # 12 hours

OPENCLAW_BIN = '/opt/homebrew/bin/openclaw'

now_ms = int(time.time() * 1000)

def log(msg: str):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with LOG_FILE.open('a') as fh:
        fh.write(f"[{timestamp}] {msg}\n")

try:
    result = subprocess.run([
        OPENCLAW_BIN, 'sessions', '--json'
    ], capture_output=True, text=True, check=True, timeout=30)
    data = json.loads(result.stdout)
except FileNotFoundError:
    log(f"openclaw binary not found at {OPENCLAW_BIN}")
    raise SystemExit(1)
except subprocess.TimeoutExpired:
    log("openclaw sessions command timed out")
    raise SystemExit(1)
except subprocess.CalledProcessError as exc:
    log(f"Failed to fetch sessions: {exc.stderr.strip() if exc.stderr else exc}")
    raise SystemExit(1)
except json.JSONDecodeError as exc:
    log(f"Failed to parse sessions JSON: {exc}")
    raise SystemExit(1)

sessions = data.get('sessions', [])
stale = []
for session in sessions:
    age_ms = now_ms - session.get('updatedAt', now_ms)
    if age_ms >= THRESHOLD_MS:
        stale.append({
            'key': session.get('key'),
            'age_hours': round(age_ms / 3600000, 2)
        })

if stale:
    for entry in stale:
        log(f"Session {entry['key']} stale for {entry['age_hours']} hours.")
else:
    log('All sessions active within threshold.')
