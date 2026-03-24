#!/bin/bash
# OpenClaw Self-Healing Watchdog v2
# Runs every 10 minutes via launchd. Detects and fixes common issues.
#
# v2 improvements:
#   - Detects LLM timeout patterns in logs and auto-restarts gateway to clear cooldowns
#   - Clears stale auth profile cooldowns
#   - Monitors for "missing tool result" transcript errors
#   - Auto-runs openclaw doctor --fix on degraded state
#   - Improved escalation path

set -uo pipefail
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/selfheal.log"
STATE_FILE="$LOG_DIR/selfheal_state.json"
MAX_LOG_LINES=5000
ERR_LOG="$HOME/.openclaw/logs/gateway.err.log"

mkdir -p "$LOG_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $1" | tee -a "$LOG_FILE"; }

# ── 0. Log Rotation ──────────────────────────────────────────────────
line_count=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
if [[ $line_count -gt $MAX_LOG_LINES ]]; then
    tail -n $((MAX_LOG_LINES / 2)) "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    log "Log rotated (was $line_count lines)"
fi

log "─── Self-heal check starting ───"

ISSUES_FOUND=0
RESTART_NEEDED=0

# ── 1. Gateway Process Check ─────────────────────────────────────────
if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
    log "✅ Gateway process running"
else
    log "❌ Gateway process not found — starting"
    openclaw gateway start 2>&1 | tail -3 >> "$LOG_FILE"
    sleep 10
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        log "✅ Gateway started successfully"
    else
        log "❌ Gateway failed to start — running doctor --fix"
        openclaw doctor --fix 2>&1 | tail -10 >> "$LOG_FILE"
        openclaw gateway start 2>&1 | tail -3 >> "$LOG_FILE"
    fi
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# ── 2. Gateway RPC Health Probe ───────────────────────────────────────
GATEWAY_PORT=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/openclaw.json')).get('gateway',{}).get('port',18789))" 2>/dev/null || echo 18789)
GATEWAY_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/openclaw.json')).get('gateway',{}).get('auth',{}).get('token',''))" 2>/dev/null || echo "")

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $GATEWAY_TOKEN" \
    "http://127.0.0.1:$GATEWAY_PORT/health" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
    log "✅ Gateway RPC healthy (HTTP $HTTP_CODE)"
else
    log "⚠️ Gateway RPC unhealthy (HTTP $HTTP_CODE)"
    RESTART_NEEDED=1
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# ── 3. LLM Timeout Detection (NEW in v2) ─────────────────────────────
# Check for recent LLM timeouts in the last 30 minutes
if [[ -f "$ERR_LOG" ]]; then
    RECENT_TIMEOUTS=$(ERR_LOG="$ERR_LOG" python3 <<'PYEOF'
from datetime import datetime, timedelta
import os, re
path = os.environ.get('ERR_LOG')
cutoff = datetime.now().astimezone() - timedelta(minutes=5)
pattern = re.compile(r"(LLM request timed out|FailoverError|model fallback decision)")
count = 0
if path and os.path.exists(path):
    with open(path) as f:
        lines = f.readlines()[-400:]
    for line in lines:
        if not pattern.search(line):
            continue
        ts = line.split(' ', 1)[0]
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if dt >= cutoff:
            count += 1
print(count)
PYEOF
)
    if [[ ${RECENT_TIMEOUTS:-0} -gt 2 ]]; then
        log "⚠️ Detected $RECENT_TIMEOUTS LLM timeouts in the last 5 minutes — clearing cooldowns"
        
        # Clear auth profile cooldowns by resetting errorCount
        python3 << 'PYEOF'
import json, os
ap_file = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")
try:
    with open(ap_file) as f:
        ap = json.load(f)
    stats = ap.get("usageStats", {})
    cleared = 0
    for profile_id, stat in stats.items():
        if stat.get("cooldownUntil") or stat.get("disabledUntil") or stat.get("errorCount", 0) > 0:
            stat.pop("cooldownUntil", None)
            stat.pop("disabledUntil", None)
            stat.pop("disabledReason", None)
            stat["errorCount"] = 0
            cleared += 1
    if cleared > 0:
        with open(ap_file, 'w') as f:
            json.dump(ap, f, indent=4)
        print(f"Cleared cooldowns for {cleared} profiles")
    else:
        print("No cooldowns to clear")
except Exception as e:
    print(f"Error clearing cooldowns: {e}")
PYEOF
        RESTART_NEEDED=1
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        log "✅ No excessive LLM timeouts"
    fi
fi

# ── 4. Transcript Error Detection (NEW in v2) ────────────────────────
if [[ -f "$ERR_LOG" ]]; then
    TRANSCRIPT_ERRORS=$(tail -50 "$ERR_LOG" 2>/dev/null | grep -c "missing tool result in session history" || echo 0)
    if [[ $TRANSCRIPT_ERRORS -gt 0 ]]; then
        log "⚠️ Detected $TRANSCRIPT_ERRORS transcript repair events (non-critical, monitoring)"
    fi
fi

# ── 5. Tailscale Check ───────────────────────────────────────────────
if command -v tailscale &>/dev/null; then
    TS_STATUS=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('BackendState',''))" 2>/dev/null || echo "unknown")
    if [[ "$TS_STATUS" == "Running" ]]; then
        log "✅ Tailscale running"
    else
        log "⚠️ Tailscale state: $TS_STATUS"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
fi

# ── 6. Disk Space Check ──────────────────────────────────────────────
DISK_PCT=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [[ $DISK_PCT -lt 90 ]]; then
    log "✅ Disk usage: ${DISK_PCT}%"
else
    log "⚠️ Disk usage HIGH: ${DISK_PCT}%"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# ── 7. Gateway Restart if Needed ─────────────────────────────────────
if [[ $RESTART_NEEDED -eq 1 ]]; then
    log "🔄 Restarting gateway to clear issues..."
    openclaw gateway restart 2>&1 | tail -5 >> "$LOG_FILE"
    sleep 15
    
    # Verify restart worked
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $GATEWAY_TOKEN" \
        "http://127.0.0.1:$GATEWAY_PORT/health" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        log "✅ Gateway restarted successfully"
    else
        log "❌ Gateway restart failed — running doctor --fix"
        openclaw doctor --fix 2>&1 | tail -10 >> "$LOG_FILE"
        openclaw gateway start 2>&1 | tail -3 >> "$LOG_FILE"
        sleep 10
    fi
fi

# ── 8. Periodic Doctor Run (every 6th check ≈ hourly) ────────────────
CHECK_COUNT=$(python3 -c "
import json, os
sf = '$STATE_FILE'
try:
    with open(sf) as f: s = json.load(f)
except: s = {}
c = s.get('check_count', 0) + 1
s['check_count'] = c
s['last_check'] = '$(ts)'
with open(sf, 'w') as f: json.dump(s, f)
print(c)
" 2>/dev/null || echo "1")

if [[ $((CHECK_COUNT % 6)) -eq 0 ]]; then
    log "🔧 Running periodic openclaw doctor --fix"
    openclaw doctor --fix 2>&1 | tail -20 >> "$LOG_FILE"
fi

log "─── Self-heal check complete ($ISSUES_FOUND issues found) ───"
