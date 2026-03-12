#!/bin/bash
set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
TARGET="5387843769"
CHANNEL="telegram"

if [[ $# -eq 0 ]]; then
  echo "Usage: notify.sh <message>" >&2
  exit 1
fi

MESSAGE="$*"
openclaw message send --channel "$CHANNEL" --target "$TARGET" --message "$MESSAGE" >/dev/null
