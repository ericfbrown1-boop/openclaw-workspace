#!/usr/bin/env bash
# cron-delivery-heal.sh — Detects cron jobs that failed due to Telegram outbound
# not being ready (gateway restart race condition) and re-triggers them.
# Designed to run every 30 minutes via OpenClaw cron.

set -euo pipefail

WORKSPACE="$HOME/.openclaw/workspace"
STATE_FILE="$WORKSPACE/memory/cron-heal-state.json"
LOG_FILE="$WORKSPACE/memory/cron-heal.log"

# Initialize state file if missing
if [ ! -f "$STATE_FILE" ]; then
  echo '{"lastHealAt":0,"healed":[]}' > "$STATE_FILE"
fi

NOW_MS=$(date +%s)000
HEALED=()

# Get cron jobs as JSON via openclaw CLI
JOBS_JSON=$(openclaw cron list --json 2>/dev/null || echo '{"jobs":[]}')

# Find jobs with "Outbound not configured" errors
FAILED_JOBS=$(echo "$JOBS_JSON" | python3 -c "
import sys, json, time
data = json.load(sys.stdin)
now_ms = int(time.time() * 1000)
for job in data.get('jobs', []):
    state = job.get('state', {})
    err = state.get('lastError', '')
    status = state.get('lastRunStatus', '')
    last_run = state.get('lastRunAtMs', 0)
    # Only heal if: error is outbound-related, happened in last 6 hours, job is enabled
    if 'Outbound not configured' in err and job.get('enabled', False):
        age_hours = (now_ms - last_run) / 3600000
        if age_hours < 6:
            print(json.dumps({'id': job['id'], 'name': job.get('name','?'), 'error': err, 'age_hours': round(age_hours,1)}))
" 2>/dev/null)

if [ -z "$FAILED_JOBS" ]; then
  echo "$(date -Iseconds) No outbound delivery failures to heal" >> "$LOG_FILE"
  echo "OK: No failed deliveries"
  exit 0
fi

COUNT=0
while IFS= read -r line; do
  JOB_ID=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  JOB_NAME=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])")

  # Check if we already healed this job in the last 2 hours (prevent loops)
  ALREADY_HEALED=$(python3 -c "
import json, time
with open('$STATE_FILE') as f:
    state = json.load(f)
now = time.time() * 1000
for h in state.get('healed', []):
    if h['id'] == '$JOB_ID' and (now - h['at']) < 7200000:
        print('yes')
        break
else:
    print('no')
")

  if [ "$ALREADY_HEALED" = "yes" ]; then
    echo "$(date -Iseconds) SKIP $JOB_NAME ($JOB_ID) — already healed recently" >> "$LOG_FILE"
    continue
  fi

  # Re-trigger the job
  echo "$(date -Iseconds) HEAL $JOB_NAME ($JOB_ID) — re-triggering after outbound failure" >> "$LOG_FILE"
  openclaw cron run "$JOB_ID" 2>/dev/null || true

  # Record the heal
  python3 -c "
import json, time
with open('$STATE_FILE') as f:
    state = json.load(f)
state['lastHealAt'] = int(time.time() * 1000)
# Keep only last 50 heal records
state['healed'] = [h for h in state.get('healed', []) if time.time()*1000 - h['at'] < 86400000]
state['healed'].append({'id': '$JOB_ID', 'name': '$JOB_NAME', 'at': int(time.time()*1000)})
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"

  COUNT=$((COUNT + 1))
  HEALED+=("$JOB_NAME")
done <<< "$FAILED_JOBS"

echo "HEALED $COUNT jobs: ${HEALED[*]}"
