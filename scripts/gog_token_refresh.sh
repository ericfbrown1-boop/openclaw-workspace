#!/bin/bash
# gog Token Refresh Wrapper
# Runs every 3 hours via LaunchAgent. Proactively refreshes Google OAuth
# tokens BEFORE they expire. Does NOT attempt browser auth.
#
# Install LaunchAgent:
#   cp com.openclaw.gog-refresh.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.openclaw.gog-refresh.plist

set -uo pipefail
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/gog_token_refresh.log"
CRON_STATE="$HOME/.openclaw/workspace/memory/cron-state.json"
AUTH_FALLBACK="$HOME/.openclaw/workspace/memory/auth-fallback-state.json"
INCIDENTS_FILE="$HOME/.openclaw/workspace/memory/incidents.jsonl"
CONFIG="$HOME/.openclaw/openclaw.json"

mkdir -p "$LOG_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $1" | tee -a "$LOG_FILE"; }

# Log rotation (keep last 500 lines)
line_count=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
if [[ $line_count -gt 500 ]]; then
    tail -n 250 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

log "─── Token refresh check starting ───"

# Step 1: Test current token with a lightweight API call
GOG_TEST=$(gog gmail search "newer_than:1d" --max 1 --account ericfbrown1@gmail.com 2>&1)
GOG_EXIT=$?

if [[ $GOG_EXIT -ne 0 ]] || echo "$GOG_TEST" | grep -q "invalid_grant\|token.*expired\|token.*revoked\|Authorization failed\|authentication failed"; then
    log "⚠️ Token test FAILED — attempting refresh"

    # Step 2: Try gog auth refresh (non-interactive)
    REFRESH_RESULT=$(gog auth refresh --account ericfbrown1@gmail.com 2>&1)
    REFRESH_EXIT=$?

    if [[ $REFRESH_EXIT -eq 0 ]]; then
        log "✅ Token refreshed successfully"

        # Verify the refresh actually worked
        VERIFY=$(gog gmail search "newer_than:1d" --max 1 --account ericfbrown1@gmail.com 2>&1)
        VERIFY_EXIT=$?
        if [[ $VERIFY_EXIT -ne 0 ]] || echo "$VERIFY" | grep -q "invalid_grant\|token.*expired\|token.*revoked"; then
            log "❌ Refresh reported success but token still broken"
        else
            log "✅ Token verified working after refresh"
            exit 0
        fi
    else
        log "❌ Token refresh failed: $REFRESH_RESULT"
    fi

    # Step 3: Refresh failed — delete stale keychain entry so it doesn't block manual reauth
    log "🗑️ Deleting stale keychain entry for ericfbrown1@gmail.com"
    security delete-generic-password -s "gog-oauth" -a "ericfbrown1@gmail.com" 2>/dev/null || true

    # Step 4: Log incident
    python3 <<PYEOF
import json
from datetime import datetime, timezone
entry = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "category": "auth",
    "severity": "warning",
    "service": "google_oauth",
    "description": "Token refresh failed — stale keychain entry deleted. Manual browser reauth required.",
    "auto_action": "Deleted keychain entry, sent Telegram alert"
}
with open("$INCIDENTS_FILE", "a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

    # Step 5: Send Telegram notification (do NOT attempt browser auth)
    TG_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('channels',{}).get('telegram',{}).get('botToken',''))" 2>/dev/null)
    TG_CHAT=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('channels',{}).get('telegram',{}).get('chatId',''))" 2>/dev/null)
    if [[ -n "$TG_TOKEN" && -n "$TG_CHAT" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
            -d chat_id="$TG_CHAT" \
            -d text="⚠️ Google token refresh failed. Stale keychain entry deleted. Fix: gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent" \
            > /dev/null 2>&1
        log "📨 Telegram alert sent"
    fi

    log "─── Token refresh FAILED — manual reauth required ───"
    exit 1
else
    log "✅ Token is valid — no refresh needed"
    log "─── Token refresh check complete ───"
    exit 0
fi
