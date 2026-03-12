#!/bin/bash
set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
THRESHOLD_SECONDS=900  # 15 minutes
PROCESS_NAME="openclaw-gateway"
LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/gateway_watchdog.log"
NOTIFY_SCRIPT="$HOME/.openclaw/workspace/scripts/notify.sh"

mkdir -p "$LOG_DIR"

time_to_seconds() {
  local time_str="$1"
  local days=0
  local hours=0
  local mins=0
  local secs=0

  if [[ "$time_str" == *-* ]]; then
    days=${time_str%%-*}
    time_str=${time_str#*-}
  fi

  IFS=':' read -r part1 part2 part3 <<< "$time_str"

  if [[ -z "$part2" && -z "$part3" ]]; then
    secs=${part1:-0}
  elif [[ -z "$part3" ]]; then
    mins=${part1:-0}
    secs=${part2:-0}
  else
    hours=${part1:-0}
    mins=${part2:-0}
    secs=${part3:-0}
  fi

  echo $((days*86400 + hours*3600 + mins*60 + secs))
}

stalled=0

while IFS= read -r line; do
  pid=$(echo "$line" | awk '{print $1}')
  stat=$(echo "$line" | awk '{print $2}')
  etime=$(echo "$line" | awk '{print $3}')

  # Flags indicating uninterruptible sleep (D), stopped (T), or zombie (Z)
  if [[ "$stat" != *D* && "$stat" != *T* && "$stat" != *Z* ]]; then
    continue
  fi

  elapsed=$(time_to_seconds "$etime")
  if [[ "$elapsed" -ge $THRESHOLD_SECONDS ]]; then
    stalled=1
    target_pid="$pid"
    target_stat="$stat"
    target_elapsed="$elapsed"
    break
  fi

done < <(ps -axo pid=,stat=,etime=,command= | grep "$PROCESS_NAME" | grep -v grep)

if [[ $stalled -eq 1 ]]; then
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  {
    echo "[$timestamp] Detected stalled process $PROCESS_NAME (pid $target_pid, stat $target_stat, ${target_elapsed}s). Restarting gateway..."
    if openclaw gateway restart; then
      [[ -x "$NOTIFY_SCRIPT" ]] && "$NOTIFY_SCRIPT" "Gateway watchdog restarted gateway (pid $target_pid, state $target_stat, ${target_elapsed}s stalled)."
    else
      echo "[$timestamp] Failed to restart gateway" >&2
      [[ -x "$NOTIFY_SCRIPT" ]] && "$NOTIFY_SCRIPT" "Gateway watchdog failed to restart gateway (pid $target_pid). Check logs."
    fi
  } | tee -a "$LOG_FILE"
else
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] No stalled $PROCESS_NAME processes detected." >> "$LOG_FILE"
fi
