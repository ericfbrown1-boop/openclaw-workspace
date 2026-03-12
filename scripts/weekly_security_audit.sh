#!/bin/bash
set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/weekly_security_audit.log"
mkdir -p "$LOG_DIR"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

{
  echo "[$(timestamp)] Starting weekly security audit..."
  openclaw security audit --deep
  echo "[$(timestamp)] Completed security audit."
  openclaw update status
  echo "[$(timestamp)] Completed update status check."
} >> "$LOG_FILE" 2>&1
