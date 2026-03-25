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

# ── 2.5 Google OAuth Health Probe ────────────────────────────────
CRON_STATE="$HOME/.openclaw/workspace/memory/cron-state.json"
AUTH_FALLBACK="$HOME/.openclaw/workspace/memory/auth-fallback-state.json"
INCIDENTS_FILE="$HOME/.openclaw/workspace/memory/incidents.jsonl"

GOG_TEST=$(gog gmail search "newer_than:1d" --max 1 --account ericfbrown1@gmail.com 2>&1)
GOG_EXIT=$?
if [[ $GOG_EXIT -ne 0 ]] || echo "$GOG_TEST" | grep -q "invalid_grant\|token.*expired\|token.*revoked\|Authorization failed\|authentication failed"; then
    log "❌ Google OAuth FAILED — switching to fallback mode"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))

    # Set circuit breaker: auth_healthy = false
    python3 <<PYEOF
import json, os
from datetime import datetime, timezone
sf = "$CRON_STATE"
try:
    with open(sf) as f: s = json.load(f)
except: s = {"cron_jobs": {}}
s["auth_healthy"] = False
s["auth_checked_at"] = datetime.now(timezone.utc).isoformat()
s["auth_failure_reason"] = "Google OAuth token expired or revoked"
with open(sf, "w") as f: json.dump(s, f, indent=2)
print("Circuit breaker set: auth_healthy=false")
PYEOF

    # Set Zapier fallback mode
    python3 <<PYEOF
import json, os
from datetime import datetime, timezone
af = "$AUTH_FALLBACK"
state = {
    "gmail": {"fallback": "zapier_mcp", "since": datetime.now(timezone.utc).isoformat(), "reason": "gog OAuth expired"},
    "calendar": {"fallback": "zapier_mcp", "since": datetime.now(timezone.utc).isoformat(), "reason": "gog OAuth expired"},
    "sheets": {"fallback": "zapier_mcp", "since": datetime.now(timezone.utc).isoformat(), "reason": "gog OAuth expired"},
    "drive": {"fallback": "zapier_mcp", "since": datetime.now(timezone.utc).isoformat(), "reason": "gog OAuth expired"}
}
with open(af, "w") as f: json.dump(state, f, indent=2)
print("Fallback state: all Google services → Zapier MCP")
PYEOF

    # Log incident
    python3 <<PYEOF
import json, os
from datetime import datetime, timezone
entry = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "category": "auth",
    "severity": "critical",
    "service": "google_oauth",
    "description": "Google OAuth token expired/revoked — circuit breaker activated, Zapier fallback enabled",
    "auto_action": "Set auth_healthy=false, enabled Zapier MCP fallback"
}
with open("$INCIDENTS_FILE", "a") as f:
    f.write(json.dumps(entry) + "\n")
print("Incident logged")
PYEOF

    # Send Telegram alert
    TG_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/openclaw.json')).get('channels',{}).get('telegram',{}).get('botToken',''))" 2>/dev/null)
    TG_CHAT=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/openclaw.json')).get('channels',{}).get('telegram',{}).get('chatId',''))" 2>/dev/null)
    if [[ -n "$TG_TOKEN" && -n "$TG_CHAT" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
            -d chat_id="$TG_CHAT" \
            -d text="🔴 Google OAuth EXPIRED — cron circuit breaker ON, Zapier fallback active. Fix: gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent" \
            > /dev/null 2>&1
        log "📨 Telegram alert sent to Eric"
    fi
else
    log "✅ Google OAuth healthy"

    # Ensure circuit breaker is clear
    python3 <<PYEOF
import json, os
from datetime import datetime, timezone
sf = "$CRON_STATE"
try:
    with open(sf) as f: s = json.load(f)
except: s = {"cron_jobs": {}}
was_broken = not s.get("auth_healthy", True)
s["auth_healthy"] = True
s["auth_checked_at"] = datetime.now(timezone.utc).isoformat()
s["auth_failure_reason"] = None
with open(sf, "w") as f: json.dump(s, f, indent=2)
if was_broken:
    print("Circuit breaker RESTORED: auth_healthy=true")
else:
    print("Circuit breaker confirmed: auth_healthy=true")
PYEOF

    # Clear fallback mode if it was active
    if [[ -f "$AUTH_FALLBACK" ]]; then
        python3 <<PYEOF
import json, os
af = "$AUTH_FALLBACK"
try:
    with open(af) as f: state = json.load(f)
    if any(v.get("fallback") for v in state.values()):
        for k in state: state[k] = {"fallback": None, "since": None, "reason": None}
        with open(af, "w") as f: json.dump(state, f, indent=2)
        print("Fallback mode CLEARED — gog auth restored")
    else:
        print("No active fallbacks to clear")
except: pass
PYEOF
    fi
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

# ── 7.5 API Usage Tracking ──────────────────────────────────────
USAGE_RESULT=$(python3 "$HOME/.openclaw/workspace/scripts/api_usage_monitor.py" 2>&1)
log "📊 $USAGE_RESULT"

# Also snapshot token usage from auth-profiles.json
python3 << 'PYEOF'
import json, os, time
from datetime import datetime, timezone

ap_file = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")
usage_log = os.path.expanduser("~/.openclaw/workspace/logs/api_usage.jsonl")

try:
    with open(ap_file) as f:
        ap = json.load(f)
    stats = ap.get("usageStats", {})
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "auth-profiles",
        "profiles": {}
    }
    for pid, stat in stats.items():
        snapshot["profiles"][pid] = {
            "error_count": stat.get("errorCount", 0),
            "last_used": stat.get("lastUsed", 0),
            "failure_counts": stat.get("failureCounts", {}),
            "in_cooldown": bool(stat.get("cooldownUntil", 0) > int(time.time() * 1000)),
            "disabled": bool(stat.get("disabledUntil", 0) > int(time.time() * 1000)),
        }
    with open(usage_log, "a") as f:
        f.write(json.dumps(snapshot) + "\n")
except Exception as e:
    print(f"Usage snapshot error: {e}")
PYEOF

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
