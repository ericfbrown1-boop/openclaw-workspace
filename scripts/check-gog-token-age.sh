#!/bin/bash
# Checks gog token and alerts if approaching 7-day expiry
# Run: bash check-gog-token-age.sh

LAST_AUTH_FILE="/Users/ericbrown/.openclaw/workspace/memory/gog-last-auth.txt"
TODAY=$(date +%s)

if [ -f "$LAST_AUTH_FILE" ]; then
    LAST_AUTH=$(cat "$LAST_AUTH_FILE")
    DAYS_OLD=$(( (TODAY - LAST_AUTH) / 86400 ))

    if [ "$DAYS_OLD" -ge 6 ]; then
        echo "⚠️ GOG TOKEN WARNING: $DAYS_OLD days old — expires in $((7 - DAYS_OLD)) day(s)!"
        echo "Run: gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent"
        exit 1
    else
        echo "✅ gog token OK ($DAYS_OLD days old, $(( 7 - DAYS_OLD )) days until expiry)"
    fi
else
    echo "⚠️ No token age record found — recording now"
    echo "$TODAY" > "$LAST_AUTH_FILE"
fi
