#!/usr/bin/env bash
# stall-respawner.sh — Detects tasks stalled >4h and alerts via Telegram.
# Run every 2h via OpenClaw cron.
# Cannot auto-spawn agents (no API), but creates actionable alerts.

set -euo pipefail

WORKSPACE="$HOME/.openclaw/workspace"
TASKS_FILE="$WORKSPACE/tasks.json"
INCIDENTS_FILE="$WORKSPACE/memory/incidents.jsonl"
LOG_FILE="$WORKSPACE/memory/stall-respawner.log"
STALL_THRESHOLD_HOURS=4

log() { echo "$(date -Iseconds) $1" >> "$LOG_FILE"; }

if [ ! -f "$TASKS_FILE" ]; then
  log "ERROR: tasks.json not found"
  echo "ERROR: tasks.json not found"
  exit 1
fi

# Find stalled tasks: status=running, progress < 100, no update in >4h
STALLED=$(python3 << PYEOF
import json, sys
from datetime import datetime, timezone, timedelta

threshold = timedelta(hours=4)
now = datetime.now(timezone.utc)

with open("$TASKS_FILE") as f:
    data = json.load(f)

tasks = data.get("tasks", {})
stalled = []

for tid, task in tasks.items():
    status = task.get("status", "")
    progress = task.get("progress", 0)
    if status != "running" or progress >= 100:
        continue

    # Check updatedAt or startedAt
    updated = task.get("updatedAt") or task.get("startedAt") or task.get("createdAt")
    if not updated:
        stalled.append({"id": tid, "title": task.get("title", tid), "progress": progress, "hours": "unknown"})
        continue

    try:
        ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age = now - ts
        if age > threshold:
            stalled.append({
                "id": tid,
                "title": task.get("title", tid),
                "progress": progress,
                "hours": round(age.total_seconds() / 3600, 1)
            })
    except Exception:
        stalled.append({"id": tid, "title": task.get("title", tid), "progress": progress, "hours": "parse-error"})

if stalled:
    for s in stalled:
        print(json.dumps(s))
else:
    print("")
PYEOF
)

if [ -z "$STALLED" ]; then
  log "OK: No stalled tasks"
  echo "OK: No stalled tasks detected"
  exit 0
fi

COUNT=0
ALERT_MSG="STALL ALERT:\n"
while IFS= read -r line; do
  [ -z "$line" ] && continue
  TITLE=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
  PROGRESS=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['progress'])")
  HOURS=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['hours'])")
  TID=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

  ALERT_MSG+="- $TITLE ($PROGRESS%) stalled ${HOURS}h\n"
  COUNT=$((COUNT + 1))

  # Log incident
  python3 -c "
import json, datetime
inc = {
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'type': 'stall_detected',
    'task_id': '$TID',
    'title': '$TITLE',
    'progress': $PROGRESS,
    'stalled_hours': '$HOURS',
    'action': 'alert_sent'
}
with open('$INCIDENTS_FILE', 'a') as f:
    f.write(json.dumps(inc) + '\n')
"

  log "STALL: $TITLE ($PROGRESS%) stalled ${HOURS}h"
done <<< "$STALLED"

ALERT_MSG+="\nAction: Eric must direct agent to resume or cancel these tasks."
echo -e "$ALERT_MSG"
echo "STALLED $COUNT tasks"
