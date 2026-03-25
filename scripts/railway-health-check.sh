#!/usr/bin/env bash
# railway-health-check.sh — Check health of Mission Control endpoints
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

check() {
  local label="$1" url="$2"
  if curl -fsS --max-time 10 "$url" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ${label} — ${url}"
  else
    echo -e "${RED}✗${NC} ${label} — ${url}"
    FAILURES+=("${label}")
  fi
}

FAILURES=()

echo "=== Mission Control Health Check ==="
echo "$(date -Iseconds)"
echo ""

echo "— Local —"
check "Frontend (local)"  "http://localhost:3000/api/health"
check "Backend  (local)"  "http://localhost:3001/health"

echo ""
echo "— Railway —"
check "Railway  (prod)"   "https://satisfied-youth-production.up.railway.app/api/health"

echo ""
if [ ${#FAILURES[@]} -eq 0 ]; then
  echo -e "${GREEN}All endpoints healthy.${NC}"
  exit 0
else
  echo -e "${RED}${#FAILURES[@]} endpoint(s) DOWN: ${FAILURES[*]}${NC}"
  exit 1
fi
