#!/bin/bash
# OpenClaw Gateway Heartbeat — lightweight 60-second health check
# Only checks if the gateway process is alive and HTTP-responsive.
# Complements the full selfheal (10 min) with faster detection.

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

LOG="$HOME/.openclaw/workspace/logs/heartbeat.log"
mkdir -p "$(dirname "$LOG")"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

rotate_if_needed() {
    local lines
    lines=$(wc -l < "$LOG" 2>/dev/null || echo 0)
    if [[ $lines -gt 2000 ]]; then
        tail -n 1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
    fi
}

# Check 1: Process alive?
if ! pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
    echo "[$(ts)] Gateway process missing — starting" >> "$LOG"
    openclaw gateway start >> "$LOG" 2>&1
    rotate_if_needed
    exit 0
fi

# Check 2: HTTP responsive? (read port+token in one python3 call)
read -r GATEWAY_PORT GATEWAY_TOKEN < <(python3 -c "
import json
c=json.load(open('$HOME/.openclaw/openclaw.json'))
g=c.get('gateway',{})
print(g.get('port',18789), g.get('auth',{}).get('token',''))
" 2>/dev/null || echo "18789 ")

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    -H "Authorization: Bearer $GATEWAY_TOKEN" \
    "http://127.0.0.1:$GATEWAY_PORT/health" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "[$(ts)] Gateway unhealthy (HTTP $HTTP_CODE) — restarting" >> "$LOG"
    openclaw gateway restart >> "$LOG" 2>&1
    rotate_if_needed
fi
