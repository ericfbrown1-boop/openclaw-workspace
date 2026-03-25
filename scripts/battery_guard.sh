#!/bin/bash
# Battery Guard — manages caffeinate-based sleep prevention on battery
# Keeps system awake via IOKit power assertion (caffeinate -dim)
# Kills the assertion at 10% battery to protect hardware.
# Runs every 5 minutes via launchd.

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
LOG="$HOME/.openclaw/workspace/logs/battery_guard.log"
mkdir -p "$(dirname "$LOG")"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

rotate_if_needed() {
    local lines
    lines=$(wc -l < "$LOG" 2>/dev/null || echo 0)
    if [[ $lines -gt 2000 ]]; then
        tail -n 1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
    fi
}

# Use pgrep instead of PID file to avoid stale-PID and orphan issues
is_guard_caffeinate_running() {
    pgrep -f "caffeinate -dim$" > /dev/null 2>&1
}

start_caffeinate() {
    if ! is_guard_caffeinate_running; then
        # -d: prevent display sleep, -i: prevent idle sleep, -m: prevent disk sleep
        /usr/bin/caffeinate -dim &
        disown
        echo "[$(ts)] Started caffeinate (PID $!) — system will stay awake" >> "$LOG"
    fi
}

stop_caffeinate() {
    local pids
    pids=$(pgrep -f "caffeinate -dim$" 2>/dev/null)
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill 2>/dev/null
        echo "[$(ts)] Stopped caffeinate — system can sleep normally" >> "$LOG"
    fi
}

# Get battery percentage and AC status in one call
BATT_OUTPUT=$(pmset -g batt)
BATT_PCT=$(echo "$BATT_OUTPUT" | grep -o '[0-9]\+%' | tr -d '%')
ON_AC=$(echo "$BATT_OUTPUT" | grep -c "AC Power")

if [[ -z "$BATT_PCT" ]]; then
    exit 0
fi

if [[ "$ON_AC" -gt 0 ]]; then
    start_caffeinate
    exit 0
fi

# On battery
if [[ "$BATT_PCT" -le 10 ]]; then
    if is_guard_caffeinate_running; then
        echo "[$(ts)] Battery at ${BATT_PCT}% — releasing caffeinate, system may sleep" >> "$LOG"
        stop_caffeinate
    fi
elif [[ "$BATT_PCT" -gt 10 ]]; then
    start_caffeinate
fi

rotate_if_needed
