#!/usr/bin/env bash
# env-parity-check.sh — Validate environment parity between local and Docker container.
# Run before any Docker deployment to catch missing deps, env vars, and hardcoded paths.
# Usage: ./env-parity-check.sh <container-name-or-id> [.env.example-path]

set -euo pipefail

CONTAINER="${1:-}"
ENV_EXAMPLE="${2:-.env.example}"
ERRORS=0
WARNINGS=0

red()    { echo -e "\033[31m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
green()  { echo -e "\033[32m$1\033[0m"; }

if [ -z "$CONTAINER" ]; then
  echo "Usage: $0 <container-name-or-id> [.env.example-path]"
  echo "Validates environment parity between host and Docker container."
  exit 1
fi

echo "=== Environment Parity Check ==="
echo "Container: $CONTAINER"
echo ""

# 1. Check container is running
if ! docker inspect "$CONTAINER" > /dev/null 2>&1; then
  red "FAIL: Container '$CONTAINER' not found or not running"
  exit 1
fi
green "PASS: Container is running"

# 2. Check .env.example vars exist in container
if [ -f "$ENV_EXAMPLE" ]; then
  echo ""
  echo "--- Checking env vars from $ENV_EXAMPLE ---"
  while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    VAR_NAME=$(echo "$line" | cut -d= -f1 | tr -d ' ')
    [ -z "$VAR_NAME" ] && continue

    # Check if var exists in container
    CONTAINER_VAL=$(docker exec "$CONTAINER" printenv "$VAR_NAME" 2>/dev/null || echo "__MISSING__")
    if [ "$CONTAINER_VAL" = "__MISSING__" ]; then
      red "FAIL: $VAR_NAME not set in container"
      ERRORS=$((ERRORS + 1))
    else
      # Check for truncated API keys (inline comment issue)
      if [[ "$VAR_NAME" == *"KEY"* || "$VAR_NAME" == *"TOKEN"* || "$VAR_NAME" == *"SECRET"* ]]; then
        LEN=${#CONTAINER_VAL}
        if [ "$LEN" -lt 20 ]; then
          yellow "WARN: $VAR_NAME looks truncated (${LEN} chars) — check for inline comments in .env"
          WARNINGS=$((WARNINGS + 1))
        fi
      fi
      green "PASS: $VAR_NAME is set (${#CONTAINER_VAL} chars)"
    fi
  done < "$ENV_EXAMPLE"
else
  yellow "WARN: No $ENV_EXAMPLE found — skipping env var check"
  WARNINGS=$((WARNINGS + 1))
fi

# 3. Check for hardcoded paths in project files
echo ""
echo "--- Checking for hardcoded paths ---"
HARDCODED=$(grep -rn '/Users/\|C:\\Users\\\|~/' --include='*.py' --include='*.js' --include='*.ts' --include='*.sh' . 2>/dev/null | grep -v node_modules | grep -v .git | grep -v __pycache__ | head -20 || true)
if [ -n "$HARDCODED" ]; then
  yellow "WARN: Found hardcoded paths (may break in container):"
  echo "$HARDCODED" | head -10
  WARNINGS=$((WARNINGS + 1))
else
  green "PASS: No hardcoded paths found"
fi

# 4. Check key binaries exist in container
echo ""
echo "--- Checking binaries in container ---"
for BIN in python3 pip curl git; do
  if docker exec "$CONTAINER" which "$BIN" > /dev/null 2>&1; then
    green "PASS: $BIN available"
  else
    yellow "WARN: $BIN not found in container"
    WARNINGS=$((WARNINGS + 1))
  fi
done

# 5. Check Python packages match (if Python project)
if docker exec "$CONTAINER" which pip > /dev/null 2>&1 && [ -f "requirements.txt" ]; then
  echo ""
  echo "--- Checking Python packages ---"
  CONTAINER_PKGS=$(docker exec "$CONTAINER" pip list --format=columns 2>/dev/null | tail -n +3 | awk '{print tolower($1)}' | sort)
  REQUIRED_PKGS=$(grep -v '^#' requirements.txt | sed 's/[>=<].*//' | tr '[:upper:]' '[:lower:]' | sed 's/_/-/g' | sort)

  MISSING=$(comm -23 <(echo "$REQUIRED_PKGS") <(echo "$CONTAINER_PKGS") | head -20)
  if [ -n "$MISSING" ]; then
    red "FAIL: Missing Python packages in container:"
    echo "$MISSING"
    ERRORS=$((ERRORS + 1))
  else
    green "PASS: All required Python packages installed"
  fi
fi

# Summary
echo ""
echo "=== Summary ==="
echo "Errors: $ERRORS | Warnings: $WARNINGS"
if [ "$ERRORS" -gt 0 ]; then
  red "DEPLOY BLOCKED: Fix $ERRORS error(s) before deploying"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  yellow "DEPLOY OK with $WARNINGS warning(s)"
  exit 0
else
  green "ALL CHECKS PASSED"
  exit 0
fi
