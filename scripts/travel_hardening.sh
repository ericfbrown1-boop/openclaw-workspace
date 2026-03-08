#!/bin/bash
# ============================================================
# OpenClaw Travel Hardening Script
# Run once before travel: sudo bash travel_hardening.sh
# Revert when home:      sudo bash travel_hardening.sh --revert
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }

if [[ $EUID -ne 0 ]]; then
  err "This script must be run with sudo: sudo bash $0"
  exit 1
fi

# ── Revert Mode ──────────────────────────────────────────────
if [[ "${1:-}" == "--revert" ]]; then
  echo "🔄 Reverting to normal (non-travel) settings..."
  echo ""

  # Restore default AC power settings
  pmset -c sleep 1 disksleep 10 standby 1 hibernatemode 3 autopoweroff 1
  pmset -c displaysleep 10 destroyfvkeyonstandby 1
  log "AC power settings restored to defaults"

  # Restore battery defaults
  pmset -b sleep 1 standby 1 tcpkeepalive 1
  log "Battery settings restored to defaults"

  # Re-enable macOS auto-updates
  defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true
  defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool true
  defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false
  defaults write /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall -bool true
  log "macOS auto-update checks re-enabled"

  # Re-enable App Store auto-update
  defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool true
  log "App Store auto-update re-enabled"

  echo ""
  echo "🏠 Normal mode restored. Welcome home!"
  warn "Remember to disable auto-login if you enabled it (System Settings > Users & Groups)"
  exit 0
fi

# ── Harden Mode ──────────────────────────────────────────────
echo "🛡️  OpenClaw Travel Hardening"
echo "================================="
echo ""

# 1. AC Power — prevent sleep/hibernation
echo "── AC Power Settings ──"
pmset -c sleep 0              # never sleep on AC
pmset -c disksleep 0          # never sleep disks
pmset -c standby 0            # no deep standby
pmset -c hibernatemode 0      # no hibernation (pure sleep if somehow triggered)
pmset -c autopoweroff 0       # no auto power off
pmset -c displaysleep 10      # display can sleep (saves panel life)
log "Sleep/hibernation disabled on AC power"

pmset -c tcpkeepalive 1       # keep network alive
pmset -c womp 1               # Wake-on-LAN enabled
pmset -c autorestart 1        # auto-restart after power failure
pmset -c powernap 1           # background tasks during display sleep
pmset -c destroyfvkeyonstandby 0  # don't destroy FileVault key
log "Network keepalive, Wake-on-LAN, auto-restart enabled"

# 2. Battery — survive power flickers
echo ""
echo "── Battery Fallback Settings ──"
pmset -b sleep 30             # 30 min on battery (was 1 min!)
pmset -b standby 0            # no deep standby on battery
pmset -b tcpkeepalive 1       # keep network alive on battery
log "Battery sleep extended to 30 minutes"

# 3. Disable macOS auto-updates (prevent surprise reboots)
echo ""
echo "── macOS Auto-Update Settings ──"
defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool false
defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool false
defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false
defaults write /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall -bool false
log "macOS auto-updates disabled (check + download + install)"

# 4. Disable App Store auto-update (prevents background app updates)
defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool false
log "App Store auto-update disabled"

# 5. Verify settings
echo ""
echo "── Verification ──"
echo ""
echo "AC Power settings:"
pmset -g custom 2>/dev/null | grep -E '^\s+(sleep|disksleep|standby|hibernatemode|autopoweroff|autorestart|womp|tcpkeepalive)' | head -10
echo ""
echo "Battery settings:"
pmset -g custom 2>/dev/null | sed -n '/Battery Power/,/^$/p' | grep -E '^\s+(sleep|standby|tcpkeepalive)' | head -5

echo ""
echo "Auto-update status:"
defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled 2>/dev/null && echo "  AutomaticCheckEnabled: $(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled)"
defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload 2>/dev/null && echo "  AutomaticDownload: $(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload)"

# 6. Summary & manual steps
echo ""
echo "================================="
echo "🛡️  Hardening Complete!"
echo "================================="
echo ""
warn "MANUAL STEPS STILL NEEDED:"
echo "  1. 🔌 Connect a UPS (APC BE425M or CyberPower CP685AVRG)"
echo "  2. 🔓 Enable auto-login: System Settings > Users & Groups > Automatic Login"
echo "     (So Mac boots to desktop after power failure, bypassing FileVault prompt)"
echo "  3. 🔄 Revert when home: sudo bash $0 --revert"
echo ""
log "Travel hardening applied. Safe travels! ✈️"
