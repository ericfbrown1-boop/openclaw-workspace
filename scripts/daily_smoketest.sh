#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# OpenClaw Daily Smoke Test v1.0
# Runs at 5:30 AM PT daily. Output consumed by 6 AM daily briefing.
#
# Focus areas:
#   1. Gateway health & version
#   2. Tailscale connectivity (high priority - frequent issues)
#   3. Telegram bot health (high priority - frequent issues)
#   4. Google OAuth token validity
#   5. Zapier MCP integration
#   6. Auth profiles & LLM provider health
#   7. Agent configuration integrity
#   8. LaunchAgent services
#   9. Disk, logs, sessions
#  10. Security & dependency alerts
#  11. Software update check
#  12. Known issues research (web)
# ══════════════════════════════════════════════════════════════════

set -uo pipefail
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

OUTPUT_DIR="$HOME/.openclaw/workspace/memory"
OUTPUT_FILE="$OUTPUT_DIR/smoketest-latest.md"
HISTORY_FILE="$OUTPUT_DIR/smoketest-$(date +%Y-%m-%d).md"
LOG_DIR="$HOME/.openclaw/workspace/logs"
CONFIG="$HOME/.openclaw/openclaw.json"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# Score tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0
FAILURES=0
ACTIONS=()

ts() { date '+%Y-%m-%d %H:%M:%S %Z'; }

check_pass() {
    echo "  ✅ $1"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

check_warn() {
    echo "  ⚠️  $1"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    WARNINGS=$((WARNINGS + 1))
}

check_fail() {
    echo "  ❌ $1"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    FAILURES=$((FAILURES + 1))
}

add_action() {
    ACTIONS+=("$1")
}

# Begin output
{
echo "# OpenClaw Daily Smoke Test"
echo "**Run:** $(ts)"
echo "**Host:** $(hostname)"
echo ""

# ── 1. GATEWAY HEALTH ────────────────────────────────────────────
echo "## 1. Gateway Health"
echo ""

# Version check
CURRENT_VER=$(openclaw --version 2>/dev/null | head -1)
LATEST_VER=$(npm info openclaw version 2>/dev/null)

if [ -n "$CURRENT_VER" ]; then
    echo "  Installed: $CURRENT_VER"
    if [ -n "$LATEST_VER" ]; then
        echo "  Latest available: $LATEST_VER"
        INSTALLED_NUM=$(echo "$CURRENT_VER" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [ "$INSTALLED_NUM" = "$LATEST_VER" ]; then
            check_pass "OpenClaw is up to date"
        else
            check_warn "Update available: $INSTALLED_NUM → $LATEST_VER"
            add_action "[UPDATE] Run: npm install -g openclaw@latest (current: $INSTALLED_NUM, available: $LATEST_VER)"
        fi
    fi
else
    check_fail "Cannot determine OpenClaw version"
    add_action "[CRITICAL] OpenClaw CLI not responding — check installation"
fi

# Gateway process
GW_PID=$(ps aux | grep "openclaw-gateway" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$GW_PID" ]; then
    check_pass "Gateway process running (pid $GW_PID)"
else
    check_fail "Gateway process NOT running"
    add_action "[CRITICAL] Gateway is down — run: openclaw gateway start"
fi

# Gateway RPC probe
GW_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('gateway',{}).get('port',18789))" 2>/dev/null || echo 18789)
GW_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('gateway',{}).get('auth',{}).get('token',''))" 2>/dev/null)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Authorization: Bearer $GW_TOKEN" "http://127.0.0.1:$GW_PORT/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    check_pass "Gateway HTTP health check passed (HTTP $HTTP_CODE)"
else
    check_fail "Gateway HTTP health check failed (HTTP $HTTP_CODE)"
    add_action "[CRITICAL] Gateway not responding on port $GW_PORT — restart: openclaw gateway restart"
fi

echo ""

# ── 2. TAILSCALE (HIGH PRIORITY) ─────────────────────────────────
echo "## 2. Tailscale Connectivity ⚡"
echo ""

TS_STATUS=$(tailscale status --json 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$TS_STATUS" ]; then
    TS_STATE=$(echo "$TS_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('BackendState','unknown'))" 2>/dev/null)
    TS_SELF_IP=$(echo "$TS_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); ips=d.get('Self',{}).get('TailscaleIPs',[]); print(ips[0] if ips else 'none')" 2>/dev/null)
    TS_HOSTNAME=$(echo "$TS_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Self',{}).get('HostName','unknown'))" 2>/dev/null)
    TS_ONLINE=$(echo "$TS_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Self',{}).get('Online',False))" 2>/dev/null)
    TS_PEERS=$(echo "$TS_STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
peers = d.get('Peer', {})
for k,v in peers.items():
    name = v.get('HostName','?')
    online = v.get('Online',False)
    ips = v.get('TailscaleIPs',['?'])
    status = '🟢 online' if online else '⚪ offline'
    print(f'    {name}: {ips[0]} ({status})')
" 2>/dev/null)

    echo "  State: $TS_STATE"
    echo "  Self: $TS_HOSTNAME ($TS_SELF_IP)"
    echo "  Online: $TS_ONLINE"
    echo "  Peers:"
    echo "$TS_PEERS"

    if [ "$TS_STATE" = "Running" ] && [ "$TS_ONLINE" = "True" ]; then
        check_pass "Tailscale running and connected ($TS_SELF_IP)"
    elif [ "$TS_STATE" = "Running" ]; then
        check_warn "Tailscale running but Online=$TS_ONLINE"
        add_action "[TAILSCALE] Check Tailscale menu bar — may need re-authentication"
    else
        check_fail "Tailscale state: $TS_STATE"
        add_action "[TAILSCALE] Tailscale not fully connected — open Tailscale app and check login status"
    fi

    # Check CLI version alignment
    TS_CLI_PATH=$(which tailscale 2>/dev/null)
    if [[ "$TS_CLI_PATH" == "/opt/homebrew/bin/tailscale" ]]; then
        check_warn "Tailscale CLI is Homebrew version — conflicts with Mac App Store app"
        add_action "[TAILSCALE] Run: brew uninstall tailscale (Homebrew CLI conflicts with App Store version)"
    else
        check_pass "Tailscale CLI: $TS_CLI_PATH (correct)"
    fi

    # Check Tailscale Funnel for voice calls
    FUNNEL_STATUS=$(tailscale funnel status 2>/dev/null)
    if echo "$FUNNEL_STATUS" | grep -q "3334\|voice"; then
        check_pass "Tailscale Funnel active (voice call webhook)"
    else
        check_warn "Tailscale Funnel not detected for voice calls"
        add_action "[TAILSCALE] Voice calls may not work — run: tailscale serve --bg 3334 && tailscale funnel --bg 3334"
    fi
else
    check_fail "Tailscale CLI cannot connect to service"
    add_action "[CRITICAL-TAILSCALE] Tailscale not running or CLI can't connect — open Tailscale.app from menu bar. If CLI conflict: brew uninstall tailscale"
fi

echo ""

# ── 3. TELEGRAM (HIGH PRIORITY) ──────────────────────────────────
echo "## 3. Telegram Bot Health ⚡"
echo ""

# Parse Telegram bot token from config
TG_ENABLED=$(python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
tg = cfg.get('channels',{}).get('telegram',{})
print('enabled' if tg.get('enabled', True) else 'disabled')
" 2>/dev/null)

if [ "$TG_ENABLED" = "enabled" ]; then
    # Check via doctor output (which probes Telegram)
    TG_PROBE=$(openclaw doctor 2>&1 | grep -i "telegram")
    if echo "$TG_PROBE" | grep -qi "ok"; then
        TG_LATENCY=$(echo "$TG_PROBE" | grep -oE '[0-9]+ms' | head -1)
        check_pass "Telegram bot responding ($TG_LATENCY)"
        
        # Check if latency is high
        TG_MS=$(echo "$TG_LATENCY" | grep -oE '[0-9]+')
        if [ -n "$TG_MS" ] && [ "$TG_MS" -gt 3000 ]; then
            check_warn "Telegram latency is high: ${TG_MS}ms (>3s)"
            add_action "[TELEGRAM] Bot response time is slow (${TG_MS}ms) — may indicate network issues or Telegram API degradation"
        fi
    else
        check_fail "Telegram bot probe failed"
        add_action "[CRITICAL-TELEGRAM] Telegram bot not responding — check bot token and network connectivity"
    fi

    # Check Telegram streaming config
    TG_STREAMING=$(python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
print(cfg.get('channels',{}).get('telegram',{}).get('streaming','off'))
" 2>/dev/null)
    
    if [ "$TG_STREAMING" = "partial" ]; then
        check_pass "Telegram streaming: partial (reduces perceived latency)"
    else
        check_warn "Telegram streaming: $TG_STREAMING (consider 'partial' for better UX)"
        add_action "[TELEGRAM] Enable streaming: set channels.telegram.streaming = 'partial' in config"
    fi

    # Check retry config
    TG_RETRIES=$(python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
print(cfg.get('channels',{}).get('telegram',{}).get('retry',{}).get('attempts',3))
" 2>/dev/null)
    
    if [ "$TG_RETRIES" -ge 5 ] 2>/dev/null; then
        check_pass "Telegram retry attempts: $TG_RETRIES"
    else
        check_warn "Telegram retry attempts: $TG_RETRIES (recommend 5+)"
        add_action "[TELEGRAM] Increase retry attempts to 5 for better message delivery reliability"
    fi
else
    check_fail "Telegram is disabled in config"
    add_action "[CRITICAL-TELEGRAM] Telegram channel is disabled — re-enable in openclaw.json"
fi

echo ""

# ── 4. GOOGLE OAUTH ──────────────────────────────────────────────
echo "## 4. Google OAuth Token"
echo ""

GOG_AUTH=$(gog auth list 2>&1)
if echo "$GOG_AUTH" | grep -q "ericfbrown1@gmail.com"; then
    TOKEN_DATE=$(echo "$GOG_AUTH" | grep "ericfbrown1" | awk '{print $4}')
    check_pass "Google OAuth token present (issued: $TOKEN_DATE)"
    
    # Test actual API call
    GMAIL_TEST=$(gog gmail search "newer_than:1d" --max 1 --account ericfbrown1@gmail.com 2>&1)
    if echo "$GMAIL_TEST" | grep -q "invalid_grant\|expired\|revoked"; then
        check_fail "Google OAuth token EXPIRED"
        add_action "[CRITICAL-OAUTH] Google token expired — run on MacBook: gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent"
    else
        check_pass "Gmail API responding"
    fi
    
    CAL_TEST=$(gog calendar list --account ericfbrown1@gmail.com 2>&1)
    if echo "$CAL_TEST" | grep -q "invalid_grant\|expired\|revoked"; then
        check_fail "Calendar API token expired"
    else
        check_pass "Calendar API responding"
    fi
else
    check_fail "No Google OAuth token found"
    add_action "[CRITICAL-OAUTH] No Google auth — run: gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent"
fi

echo ""

# ── 5. ZAPIER MCP ────────────────────────────────────────────────
echo "## 5. Zapier MCP Integration"
echo ""

MCP_LIST=$(mcporter list 2>&1)
if echo "$MCP_LIST" | grep -q "zapier"; then
    MCP_TOOLS=$(echo "$MCP_LIST" | grep -oE '[0-9]+ tools' | head -1)
    check_pass "Zapier MCP server healthy ($MCP_TOOLS)"
else
    check_warn "Zapier MCP may not be responding"
    add_action "[MCP] Check Zapier MCP connection — run: mcporter list"
fi

echo ""

# ── 6. AUTH PROFILES & LLM PROVIDERS ─────────────────────────────
echo "## 6. LLM Provider Health"
echo ""

python3 << 'PYEOF'
import json, os, time

ap_file = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")
try:
    with open(ap_file) as f:
        ap = json.load(f)
    
    profiles = ap.get('profiles', {})
    stats = ap.get('usageStats', {})
    now = int(time.time() * 1000)
    
    for pid in profiles:
        stat = stats.get(pid, {})
        provider = profiles[pid].get('provider', '?')
        
        cooldown = stat.get('cooldownUntil')
        disabled = stat.get('disabledUntil')
        errors = stat.get('errorCount', 0)
        last_used = stat.get('lastUsed', 0)
        
        age_hours = (now - last_used) / 3600000 if last_used else -1
        
        issues = []
        if cooldown and cooldown > now:
            issues.append(f"IN COOLDOWN until {cooldown}")
        if disabled and disabled > now:
            issues.append(f"DISABLED until {disabled}")
        if errors > 3:
            issues.append(f"{errors} errors")
        
        if issues:
            print(f"  ⚠️  {pid} ({provider}): {', '.join(issues)}")
        else:
            age_str = f"{age_hours:.1f}h ago" if age_hours >= 0 else "never"
            print(f"  ✅ {pid} ({provider}): healthy, last used {age_str}")

except Exception as e:
    print(f"  ❌ Cannot read auth profiles: {e}")
PYEOF

# Check LLM timeout config
LLM_TIMEOUT=$(python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
print(cfg.get('agents',{}).get('defaults',{}).get('timeoutSeconds',600))
" 2>/dev/null)

if [ "$LLM_TIMEOUT" -le 300 ] 2>/dev/null; then
    check_pass "LLM timeout: ${LLM_TIMEOUT}s (good — fast failover)"
else
    check_warn "LLM timeout: ${LLM_TIMEOUT}s (high — consider reducing to 180s)"
    add_action "[STABILITY] Reduce LLM timeout from ${LLM_TIMEOUT}s to 180s for faster failover"
fi

# Check recent LLM timeouts in error log
ERR_LOG="$HOME/.openclaw/logs/gateway.err.log"
if [ -f "$ERR_LOG" ]; then
    RECENT_TIMEOUTS=$(tail -500 "$ERR_LOG" 2>/dev/null | grep -c "LLM request timed out\|FailoverError" || echo 0)
    if [ "$RECENT_TIMEOUTS" -gt 5 ]; then
        check_warn "$RECENT_TIMEOUTS LLM timeouts in recent logs"
        add_action "[STABILITY] Frequent LLM timeouts detected ($RECENT_TIMEOUTS) — may indicate provider issues or overloaded API"
    elif [ "$RECENT_TIMEOUTS" -gt 0 ]; then
        check_pass "Minor LLM timeouts: $RECENT_TIMEOUTS (within normal range)"
    else
        check_pass "No LLM timeouts in recent logs"
    fi
fi

echo ""

# ── 6.5 API USAGE & BUDGET ──────────────────────────────────────
echo "## 6.5 API Usage & Budget"
echo ""

# Run usage monitor to get fresh data
python3 "$HOME/.openclaw/workspace/scripts/api_usage_monitor.py" > /dev/null 2>&1

API_STATE="$HOME/.openclaw/workspace/memory/api-usage-state.json"
if [ -f "$API_STATE" ]; then
    python3 << 'PYEOF'
import json, os

state_file = os.path.expanduser("~/.openclaw/workspace/memory/api-usage-state.json")
try:
    with open(state_file) as f:
        s = json.load(f)

    monthly_cost = s.get("monthly_cost_usd", 0)
    monthly_limit = s.get("monthly_limit_usd", 100)
    monthly_pct = s.get("monthly_pct", 0)
    daily_cost = s.get("daily_cost_usd", 0)
    projected = s.get("projected_monthly_usd", 0)
    days_remaining = s.get("days_remaining", 0)
    alert_level = s.get("alert_level", "none")
    daily_tokens = s.get("daily_tokens", {})
    monthly_tokens = s.get("monthly_tokens", {})

    di = daily_tokens.get("input_tokens", 0)
    do = daily_tokens.get("output_tokens", 0)
    mi = monthly_tokens.get("input_tokens", 0)
    mo = monthly_tokens.get("output_tokens", 0)

    print(f"  Monthly spend: ${monthly_cost:.2f} / ${monthly_limit:.2f} ({monthly_pct}%)")
    print(f"  Today's spend: ${daily_cost:.4f}")
    print(f"  Projected monthly: ${projected:.2f}")
    print(f"  Days remaining: {days_remaining}")
    print(f"  Daily tokens: {di:,} in / {do:,} out")
    print(f"  Monthly tokens: {mi:,} in / {mo:,} out")
    print(f"  Alert level: {alert_level}")

    if monthly_pct >= 90:
        print(f"  ❌ CRITICAL: Budget at {monthly_pct}% — non-essential work should pause")
    elif monthly_pct >= 75:
        print(f"  ⚠️  WARNING: Budget at {monthly_pct}% — downgrade to Sonnet for non-critical tasks")
    elif monthly_pct >= 50:
        print(f"  ⚠️  INFO: Budget at {monthly_pct}% — monitor closely")
    else:
        print(f"  ✅ Budget healthy ({monthly_pct}% used)")

except Exception as e:
    print(f"  ❌ Cannot read API usage state: {e}")
PYEOF

    # Track in check counts
    API_PCT=$(python3 -c "import json; print(json.load(open('$API_STATE')).get('monthly_pct', 0))" 2>/dev/null || echo "0")
    if python3 -c "exit(0 if float('$API_PCT') < 75 else 1)" 2>/dev/null; then
        check_pass "API budget within limits ($API_PCT%)"
    elif python3 -c "exit(0 if float('$API_PCT') < 90 else 1)" 2>/dev/null; then
        check_warn "API budget at warning level ($API_PCT%)"
        add_action "[BUDGET] API spend at $API_PCT% — consider downgrading non-critical agents to Sonnet"
    else
        check_fail "API budget CRITICAL ($API_PCT%)"
        add_action "[CRITICAL-BUDGET] API spend at $API_PCT% — pause non-essential work immediately"
    fi
else
    check_warn "API usage state file not found — run api_usage_monitor.py"
    add_action "[BUDGET] Initialize API usage monitoring: python3 scripts/api_usage_monitor.py"
fi

echo ""

# ── 7. AGENT CONFIGURATION ──────────────────────────────────────
echo "## 7. Agent Configuration"
echo ""

python3 << 'PYEOF'
import json

with open('/Users/ericbrown/.openclaw/openclaw.json') as f:
    cfg = json.load(f)

agents = cfg.get('agents', {}).get('list', [])
defaults = cfg.get('agents', {}).get('defaults', {})

print(f"  Agents: {len(agents)}")
for a in agents:
    aid = a.get('id', '?')
    model = a.get('model', {})
    if isinstance(model, str):
        primary = model
        fb = 0
    else:
        primary = model.get('primary', '?')
        fb = len(model.get('fallbacks', []))
    
    ws = a.get('workspace', '')
    ws_exists = __import__('os').path.isdir(ws) if ws else False
    ws_status = "✅" if ws_exists else "❌ MISSING"
    
    if fb == 0:
        print(f"  ⚠️  {aid}: {primary} (NO fallbacks) workspace={ws_status}")
    else:
        print(f"  ✅ {aid}: {primary} +{fb} fallbacks workspace={ws_status}")
PYEOF

echo ""

# ── 8. LAUNCHAGENT SERVICES ──────────────────────────────────────
echo "## 8. LaunchAgent Services"
echo ""

launchctl list 2>/dev/null | grep -E "openclaw|ai\.openclaw" | while read pid exit label; do
    if [ "$exit" = "0" ] || [ "$pid" != "-" ]; then
        echo "  ✅ $label (exit=$exit, pid=$pid)"
    else
        echo "  ⚠️  $label (exit=$exit)"
    fi
done

echo ""

# ── 9. DISK, LOGS, SESSIONS ─────────────────────────────────────
echo "## 9. System Resources"
echo ""

DISK_PCT=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
DISK_FREE=$(df -h / | tail -1 | awk '{print $4}')
if [ "$DISK_PCT" -lt 80 ]; then
    check_pass "Disk: ${DISK_PCT}% used ($DISK_FREE free)"
elif [ "$DISK_PCT" -lt 90 ]; then
    check_warn "Disk: ${DISK_PCT}% used ($DISK_FREE free)"
    add_action "[DISK] Disk usage at ${DISK_PCT}% — consider cleanup"
else
    check_fail "Disk: ${DISK_PCT}% used ($DISK_FREE free) — CRITICAL"
    add_action "[CRITICAL-DISK] Disk almost full (${DISK_PCT}%) — immediate cleanup needed"
fi

LOG_SIZE=$(du -sh "$HOME/.openclaw/logs/" 2>/dev/null | awk '{print $1}')
check_pass "Log directory: $LOG_SIZE"

SESSION_SIZE=$(du -sh "$HOME/.openclaw/agents/main/sessions/" 2>/dev/null | awk '{print $1}')
check_pass "Session store: $SESSION_SIZE"

# Check uptime
UPTIME=$(uptime | sed 's/.*up /up /' | sed 's/,.*//')
echo "  System: $UPTIME"

echo ""

# ── 10. SECURITY ─────────────────────────────────────────────────
echo "## 10. Security"
echo ""

# Dependabot alerts
DEPENDABOT=$(gh api repos/ericfbrown1-boop/ContractAnalyzer/dependabot/alerts --jq '.[].security_advisory.severity' 2>/dev/null)
CRIT_COUNT=$(echo "$DEPENDABOT" | grep -c "critical" 2>/dev/null || true); CRIT_COUNT=${CRIT_COUNT// /}; CRIT_COUNT=${CRIT_COUNT:-0}
HIGH_COUNT=$(echo "$DEPENDABOT" | grep -c "high" 2>/dev/null || true); HIGH_COUNT=${HIGH_COUNT// /}; HIGH_COUNT=${HIGH_COUNT:-0}

if [ "$CRIT_COUNT" -gt 0 ]; then
    check_fail "Dependabot: $CRIT_COUNT critical alerts"
    add_action "[SECURITY] $CRIT_COUNT critical Dependabot alerts in ContractAnalyzer — patch immediately"
elif [ "$HIGH_COUNT" -gt 0 ]; then
    check_warn "Dependabot: $HIGH_COUNT high alerts"
    add_action "[SECURITY] $HIGH_COUNT high-severity Dependabot alerts — review and patch"
else
    check_pass "No critical/high Dependabot alerts"
fi

echo ""

# ── 11. SOFTWARE UPDATES ─────────────────────────────────────────
echo "## 11. Software Updates"
echo ""

# Node.js
NODE_VER=$(node --version 2>/dev/null)
check_pass "Node.js: $NODE_VER"

# npm
NPM_VER=$(npm --version 2>/dev/null)
check_pass "npm: $NPM_VER"

# mcporter
MCP_VER=$(mcporter --version 2>/dev/null | head -1)
check_pass "mcporter: $MCP_VER"

# gog
GOG_VER=$(gog --version 2>/dev/null | head -1)
check_pass "gog CLI: $GOG_VER"

echo ""


# ── 12. AGENT SKILLS CHANGES ─────────────────────────────────────
echo "## 12. Agent Skills & Configuration Changes"
echo ""

# Run the agent changes tracker
python3 /Users/ericbrown/.openclaw/workspace/scripts/agent_changes_tracker.py 2>/dev/null
AGENT_CHANGES=$(cat "$HOME/.openclaw/workspace/memory/agent-changes-latest.md" 2>/dev/null)
if echo "$AGENT_CHANGES" | grep -q "Modified"; then
    check_warn "Agent configuration files have been modified since last check"
    add_action "[AGENTS] Review agent configuration changes in the Agent Skills section above"
else
    check_pass "No unexpected agent configuration changes"
fi

echo ""
# ── SUMMARY ──────────────────────────────────────────────────────
echo "## Summary"
echo ""
SCORE=$((PASSED_CHECKS * 100 / (TOTAL_CHECKS > 0 ? TOTAL_CHECKS : 1)))
echo "**Health Score: ${SCORE}/100** (${PASSED_CHECKS}/${TOTAL_CHECKS} checks passed, ${WARNINGS} warnings, ${FAILURES} failures)"
echo ""

if [ ${#ACTIONS[@]} -gt 0 ]; then
    echo "## 🔔 Action Items for Eric"
    echo ""
    for i in "${!ACTIONS[@]}"; do
        echo "$((i+1)). ${ACTIONS[$i]}"
    done
else
    echo "## ✅ No Action Items"
    echo "All checks passed. System is healthy."
fi

echo ""
echo "---"
echo "*Generated by OpenClaw Daily Smoke Test v1.0 at $(ts)*"

} > "$OUTPUT_FILE" 2>&1

# Also save to dated history file
cp "$OUTPUT_FILE" "$HISTORY_FILE"

# Print to stdout for cron capture
cat "$OUTPUT_FILE"
