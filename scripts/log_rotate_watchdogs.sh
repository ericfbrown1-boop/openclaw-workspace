#!/bin/bash
set -euo pipefail

LOG_DIR="$HOME/.openclaw/workspace/logs"
MAX_SIZE=$((5 * 1024 * 1024))
mkdir -p "$LOG_DIR"

cd "$LOG_DIR"

for logfile in gateway_watchdog.log tailscale_monitor.log weekly_security_audit.log session_activity_monitor.log voice_bootstrap.log; do
  if [[ -f "$logfile" ]]; then
    size=$(stat -f %z "$logfile" 2>/dev/null || echo 0)
    if (( size > MAX_SIZE )); then
      timestamp=$(date '+%Y%m%d-%H%M%S')
      mv "$logfile" "$logfile.$timestamp"
      gzip "$logfile.$timestamp"
      touch "$logfile"
      echo "Rotated $logfile at $timestamp" >> log_rotation_history.log
    fi
  fi
done
