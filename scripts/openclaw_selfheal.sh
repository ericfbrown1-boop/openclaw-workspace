#!/bin/bash
# OpenClaw Self-Healing Watchdog
# Runs every 10 minutes via launchd. Detects and fixes common issues
# so OpenClaw stays healthy while Eric is away.
#
# Checks:
#   1. Gateway process alive + responding to RPC
#   2. WebSocket probe (actual connectivity)
#   3. openclaw doctor --fix (auto-repair)
#   4. Tailscale connectivity (for voice calls, Remote Coder)
#   5. Disk space check
#   6. Log rotation (prevent /tmp from filling up)
#
# Escalation: restart gateway → doctor --fix → force restart → log alert

set -uo pipefail
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/selfheal.log"
STATE_FILE="$LOG_DIR/selfheal_state.json"
NOTIFY_SCRIPT="$HOME/.openclaw/workspace/scripts/notify.sh"
MAX_LOG_LINES=5000

mkdir -p "$LOG_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
    echo "[$(ts)] $1" | tee -a "$LOG_FILE"
}

notify() {
    log "ALERT: $1"
    [[ -x "$NOTIFY_SCRIPT" ]] && "$NOTIFY_SCRIPT" "🛡️ Self-Heal: $1" 2>/dev/null || true
}

# ── 1. Gateway Process Check ─────────────────────────────────────────
check_gateway_process() {
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        return 0
    else
        log "Gateway process not found"
        return 1
    fi
}

# ── 2. Gateway RPC Probe ─────────────────────────────────────────────
check_gateway_rpc() {
    local result
    result=$(openclaw gateway status 2>&1)
    if echo "$result" | grep -q "RPC probe: ok"; then
        return 0
    else
        log "Gateway RPC probe failed"
        return 1
    fi
}

# ── 3. WebSocket Connectivity ─────────────────────────────────────────
check_websocket() {
    # Quick HTTP check on the gateway port
    if curl -sf -o /dev/null -m 5 "http://127.0.0.1:18789/" 2>/dev/null; then
        return 0
    else
        log "Gateway HTTP probe failed on port 18789"
        return 1
    fi
}

# ── 4. Tailscale Check ───────────────────────────────────────────────
check_tailscale() {
    if command -v tailscale &>/dev/null; then
        local status
        status=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('BackendState',''))" 2>/dev/null)
        if [[ "$status" == "Running" ]]; then
            return 0
        else
            log "Tailscale not running (state: $status)"
            return 1
        fi
    else
        return 0  # Tailscale not installed, skip
    fi
}

# ── 5. Disk Space Check ──────────────────────────────────────────────
check_disk_space() {
    local pct
    pct=$(df -h / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
    if [[ "$pct" -gt 90 ]]; then
        log "Disk usage critical: ${pct}%"
        # Clean up old OpenClaw logs
        find /tmp/openclaw -name "*.log" -mtime +3 -delete 2>/dev/null || true
        find "$LOG_DIR" -name "*.log" -size +10M -exec truncate -s 1M {} \; 2>/dev/null || true
        notify "Disk usage at ${pct}%. Cleaned old logs."
        return 1
    fi
    return 0
}

# ── 6. Log Rotation ──────────────────────────────────────────────────
rotate_logs() {
    # Trim selfheal log if too long
    if [[ -f "$LOG_FILE" ]]; then
        local lines
        lines=$(wc -l < "$LOG_FILE")
        if [[ "$lines" -gt "$MAX_LOG_LINES" ]]; then
            tail -n 2000 "$LOG_FILE" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "$LOG_FILE"
            log "Rotated selfheal log (was $lines lines)"
        fi
    fi
    # Clean OpenClaw daily logs older than 7 days
    find /tmp/openclaw -name "openclaw-*.log" -mtime +7 -delete 2>/dev/null || true
}

# ── Restart Gateway ──────────────────────────────────────────────────
restart_gateway() {
    log "Attempting gateway restart..."
    if openclaw gateway restart 2>&1 | tee -a "$LOG_FILE"; then
        sleep 10  # Give it time to come up
        if check_gateway_rpc; then
            log "Gateway restarted successfully"
            notify "Gateway was down, restarted successfully."
            return 0
        fi
    fi
    log "Gateway restart failed"
    return 1
}

# ── Run Doctor ────────────────────────────────────────────────────────
run_doctor() {
    log "Running openclaw doctor --fix..."
    local output
    output=$(openclaw doctor --fix --non-interactive 2>&1)
    echo "$output" >> "$LOG_FILE"
    # Save latest doctor output for daily briefing
    echo "$output" > "$HOME/.openclaw/workspace/memory/doctor-output-latest.txt"
    return 0
}

# ── Force Restart (nuclear option) ────────────────────────────────────
force_restart() {
    log "Force-killing and restarting gateway..."
    pkill -9 -f "openclaw.*gateway" 2>/dev/null || true
    sleep 5
    # Restart via launchd
    launchctl kickstart -k "gui/$(id -u)/ai.openclaw.gateway" 2>/dev/null || \
        openclaw gateway start 2>&1 | tee -a "$LOG_FILE"
    sleep 15
    if check_gateway_rpc; then
        log "Force restart succeeded"
        notify "Gateway force-restarted after multiple failures."
        return 0
    else
        notify "⚠️ CRITICAL: Gateway unrecoverable after force restart. Manual intervention needed."
        return 1
    fi
}

# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

log "─── Self-heal check starting ───"

# Always rotate logs first
rotate_logs

# Check disk space
check_disk_space

# Check Tailscale
if ! check_tailscale; then
    notify "Tailscale is not running. Voice calls and Remote Coder won't work."
fi

# Gateway health — escalating recovery
gateway_ok=false

if check_gateway_process && check_gateway_rpc && check_websocket; then
    gateway_ok=true
    log "Gateway healthy ✓"
else
    log "Gateway unhealthy — starting recovery..."

    # Level 1: Simple restart
    if restart_gateway; then
        gateway_ok=true
    else
        # Level 2: Doctor fix
        run_doctor
        sleep 5
        if check_gateway_rpc; then
            gateway_ok=true
            log "Doctor fix resolved the issue"
        else
            # Level 3: Force restart
            if force_restart; then
                gateway_ok=true
            fi
        fi
    fi
fi

# Run doctor periodically even when healthy (every 6 hours = ~36 checks at 10min intervals)
# Use state file to track last doctor run
if $gateway_ok; then
    last_doctor=0
    if [[ -f "$STATE_FILE" ]]; then
        last_doctor=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('last_doctor',0))" 2>/dev/null || echo 0)
    fi
    now=$(date +%s)
    elapsed=$((now - last_doctor))
    if [[ "$elapsed" -gt 21600 ]]; then  # 6 hours
        run_doctor
        python3 -c "import json; json.dump({'last_doctor': $(date +%s), 'last_check': $(date +%s)}, open('$STATE_FILE','w'))"
    else
        python3 -c "
import json, os
state = {}
if os.path.exists('$STATE_FILE'):
    state = json.load(open('$STATE_FILE'))
state['last_check'] = $(date +%s)
json.dump(state, open('$STATE_FILE','w'))
" 2>/dev/null
    fi
fi

log "─── Self-heal check complete ───"
