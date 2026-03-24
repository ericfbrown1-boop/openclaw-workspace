#!/bin/bash
set -euo pipefail

TARGET_HOST="ericf@100.67.128.123"
DEFAULT_REMOTE_PATH="C:/Users/ericf/JarvisMissionControl"

usage() {
  cat >&2 <<USAGE
Usage: $0 [-p <remote_path>] -- <command>
  -p, --path   Remote working directory (default: $DEFAULT_REMOTE_PATH)
Examples:
  $0 -- "npm run build"
  $0 -p C:/Users/ericf/JarvisReports -- "python report.py"
USAGE
  exit 1
}

REMOTE_PATH="$DEFAULT_REMOTE_PATH"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--path)
      REMOTE_PATH="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  usage
fi

CMD="$*"

POWERSHELL_CMD="Set-Location -LiteralPath '$REMOTE_PATH'; if (Test-Path .git) { git status -sb | Out-Null }; $CMD"

ssh "$TARGET_HOST" "powershell.exe -NoLogo -NoProfile -Command \"$POWERSHELL_CMD\""
