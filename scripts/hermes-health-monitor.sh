#!/bin/bash
# Hermes Supervisor — OpenClaw Health Monitor (Phase 2)
# Runs every 30 seconds, checks gateway health, auto-recovers after 3 failures
# Designed to be called by Hermes cron or launchd

set -uo pipefail

LOG_FILE="$HOME/.openclaw/workspace/memory/hermes-supervisor.log"
STATE_FILE="$HOME/.openclaw/workspace/memory/hermes-health-state.json"
MAX_FAILURES=3
MAX_RECOVERY_ATTEMPTS=3

mkdir -p "$(dirname "$LOG_FILE")"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log() {
    echo "[$(timestamp)] $1" >> "$LOG_FILE"
}

# Initialize state file if missing
if [ ! -f "$STATE_FILE" ]; then
    cat > "$STATE_FILE" << 'EOF'
{
  "consecutive_failures": 0,
  "recovery_attempts": 0,
  "last_check": null,
  "last_status": "unknown",
  "last_recovery": null,
  "total_checks": 0,
  "total_recoveries": 0,
  "learning_log": []
}
EOF
fi

# Read current state
FAILURES=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('consecutive_failures', 0))" 2>/dev/null || echo "0")
RECOVERY_ATTEMPTS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('recovery_attempts', 0))" 2>/dev/null || echo "0")

# Health check 1: Gateway process running?
GW_STATUS="unknown"
if openclaw gateway status 2>/dev/null | grep -q "running"; then
    GW_STATUS="running"
else
    GW_STATUS="down"
fi

# Health check 2: WebSocket probe
WS_STATUS="unknown"
if command -v websocat &>/dev/null; then
    if echo '{"type":"ping"}' | timeout 5 websocat ws://127.0.0.1:18789 2>/dev/null; then
        WS_STATUS="ok"
    else
        WS_STATUS="fail"
    fi
else
    # Fallback: curl HTTP probe
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/ 2>/dev/null | grep -qE "^(200|301|302|404)$"; then
        WS_STATUS="ok"
    else
        WS_STATUS="fail"
    fi
fi

# Health check 3: Recent errors in gateway log
RECENT_ERRORS=0
GW_LOG="$HOME/.openclaw/logs/gateway.log"
if [ -f "$GW_LOG" ]; then
    FIVE_MIN_AGO=$(date -v-5M +"%Y-%m-%d %H:%M" 2>/dev/null || date -d "5 minutes ago" +"%Y-%m-%d %H:%M" 2>/dev/null || echo "")
    if [ -n "$FIVE_MIN_AGO" ]; then
        RECENT_ERRORS=$(tail -200 "$GW_LOG" 2>/dev/null | grep -ci "error\\|fatal\\|crash\\|SIGTERM\\|uncaught" 2>/dev/null); RECENT_ERRORS=${RECENT_ERRORS:-0}
    fi
fi

# Determine overall health
HEALTHY=true
REASON=""

if [ "$GW_STATUS" != "running" ]; then
    HEALTHY=false
    REASON="Gateway not running"
elif [ "$WS_STATUS" == "fail" ]; then
    HEALTHY=false
    REASON="WebSocket/HTTP probe failed"
elif [ "$RECENT_ERRORS" -gt 5 ]; then
    HEALTHY=false
    REASON="$RECENT_ERRORS errors in gateway log (last 5 min)"
fi

if [ "$HEALTHY" = true ]; then
    # Reset failure counter on success
    python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    d = json.load(f)
d['consecutive_failures'] = 0
d['recovery_attempts'] = 0
d['last_check'] = '$(timestamp)'
d['last_status'] = 'healthy'
d['total_checks'] = d.get('total_checks', 0) + 1
with open('$STATE_FILE', 'w') as f:
    json.dump(d, f, indent=2)
"
    # Only log every 10th healthy check to avoid log spam
    TOTAL=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('total_checks', 0))" 2>/dev/null || echo "1")
    if [ $((TOTAL % 10)) -eq 0 ]; then
        log "[STATUS] OK — gateway=$GW_STATUS probe=$WS_STATUS errors=$RECENT_ERRORS (check #$TOTAL)"
    fi
else
    # Increment failure counter
    NEW_FAILURES=$((FAILURES + 1))
    python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    d = json.load(f)
d['consecutive_failures'] = $NEW_FAILURES
d['last_check'] = '$(timestamp)'
d['last_status'] = 'unhealthy'
d['total_checks'] = d.get('total_checks', 0) + 1
with open('$STATE_FILE', 'w') as f:
    json.dump(d, f, indent=2)
"
    log "[ALERT] Failure #$NEW_FAILURES — $REASON (gateway=$GW_STATUS probe=$WS_STATUS errors=$RECENT_ERRORS)"

    # Auto-recovery after MAX_FAILURES consecutive failures
    if [ "$NEW_FAILURES" -ge "$MAX_FAILURES" ]; then
        if [ "$RECOVERY_ATTEMPTS" -lt "$MAX_RECOVERY_ATTEMPTS" ]; then
            NEW_RECOVERY=$((RECOVERY_ATTEMPTS + 1))
            RECOVERY_START=$(date +%s)
            log "[RECOVERY] Attempt #$NEW_RECOVERY — restarting OpenClaw gateway..."

            # Attempt restart
            openclaw gateway restart 2>&1 | while read -r line; do
                log "[RECOVERY] $line"
            done

            # Wait for gateway to come back
            sleep 10

            # Verify
            if openclaw gateway status 2>/dev/null | grep -q "running"; then
                RECOVERY_END=$(date +%s)
                RECOVERY_TIME=$((RECOVERY_END - RECOVERY_START))
                log "[RECOVERY] SUCCESS — gateway back online in ${RECOVERY_TIME}s"

                python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    d = json.load(f)
d['consecutive_failures'] = 0
d['recovery_attempts'] = 0
d['last_recovery'] = '$(timestamp)'
d['total_recoveries'] = d.get('total_recoveries', 0) + 1
# Learning log — track recovery times for pattern analysis
learning = d.get('learning_log', [])
learning.append({
    'timestamp': '$(timestamp)',
    'reason': '$REASON',
    'recovery_time_seconds': $RECOVERY_TIME,
    'attempt': $NEW_RECOVERY
})
# Keep last 50 entries
d['learning_log'] = learning[-50:]
with open('$STATE_FILE', 'w') as f:
    json.dump(d, f, indent=2)
"
            else
                log "[RECOVERY] FAILED — gateway still not responding after restart"
                python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    d = json.load(f)
d['recovery_attempts'] = $NEW_RECOVERY
with open('$STATE_FILE', 'w') as f:
    json.dump(d, f, indent=2)
"
            fi
        else
            log "[ESCALATION_NOTICE] Recovery exhausted ($MAX_RECOVERY_ATTEMPTS attempts). Manual intervention required."
            # Don't keep retrying — wait for human or external fix
        fi
    fi
fi
