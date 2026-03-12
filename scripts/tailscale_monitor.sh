#!/bin/bash
set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
LOG_DIR="$HOME/.openclaw/workspace/logs"
LOG_FILE="$LOG_DIR/tailscale_monitor.log"
NOTIFY_SCRIPT="$HOME/.openclaw/workspace/scripts/notify.sh"
PORT="3334"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

start_tailscale() {
  log "Attempting to start Tailscale daemon..."
  if tailscale up >/tmp/tailscale_monitor.out 2>&1; then
    log "Tailscale daemon started."
  else
    log "Failed to start Tailscale daemon: $(cat /tmp/tailscale_monitor.out)"
    return 1
  fi
}

ensure_funnel() {
  log "Ensuring Tailscale serve/funnel on port $PORT..."
  tailscale serve --bg "$PORT" >/tmp/tailscale_monitor.out 2>&1 || log "serve output: $(cat /tmp/tailscale_monitor.out)"
  tailscale funnel --bg "$PORT" >/tmp/tailscale_monitor.out 2>&1 || log "funnel output: $(cat /tmp/tailscale_monitor.out)"
}

if ! tailscale status >/tmp/tailscale_monitor.out 2>&1; then
  log "Tailscale daemon not running."
  start_tailscale || exit 1
else
  log "Tailscale daemon is running."
fi

if ! tailscale funnel status >/tmp/tailscale_monitor.out 2>&1; then
  log "Funnel inactive; restarting."
  ensure_funnel
else
  if grep -q "off" /tmp/tailscale_monitor.out; then
    log "Funnel reported off; restarting."
    ensure_funnel
  else
    log "Funnel already active."
  fi
fi

rm -f /tmp/tailscale_monitor.out
