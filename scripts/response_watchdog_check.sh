#!/bin/bash
# Response Delivery Watchdog — detects "typing started, never responded" stalls
# Called from selfheal.sh every 10 minutes

GW_LOG="$HOME/.openclaw/logs/gateway.log"
STATE_FILE="$HOME/.openclaw/workspace/memory/response-watchdog-state.json"
STALL_THRESHOLD_MIN=5

# Find the most recent "typing TTL reached" event
LAST_TTL=$(grep "typing TTL reached" "$GW_LOG" 2>/dev/null | tail -1)

if [ -z "$LAST_TTL" ]; then
    exit 0  # No TTL events, all good
fi

# Extract timestamp
TTL_TS=$(echo "$LAST_TTL" | grep -oE '202[0-9]-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}')

if [ -z "$TTL_TS" ]; then
    exit 0
fi

# Check if there was a successful response AFTER the TTL event
LAST_RESPONSE=$(grep -E "agent model|res.*agent|message.*deliver" "$GW_LOG" 2>/dev/null | tail -1)
RESP_TS=$(echo "$LAST_RESPONSE" | grep -oE '202[0-9]-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}')

# If the TTL is more recent than any response, we have a stall
if [ -n "$TTL_TS" ] && [ -n "$RESP_TS" ]; then
    if [[ "$TTL_TS" > "$RESP_TS" ]]; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) STALL DETECTED: typing TTL at $TTL_TS, last response at $RESP_TS"
        # Write state for monitor to pick up
        cat > "$STATE_FILE" << STATEEOF
{
  "stall_detected": true,
  "typing_ttl_at": "$TTL_TS",
  "last_response_at": "$RESP_TS",
  "detected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "action": "alert_sent"
}
STATEEOF
    fi
fi
