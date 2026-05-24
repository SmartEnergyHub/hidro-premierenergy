#!/usr/bin/env bash
# Fail if secrets or runtime artifacts are tracked
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0

echo "==> Checking forbidden filenames..."
FORBIDDEN=(
  secrets.json
  token.txt
  session.json
  cookies_import.json
  browser_profile
)
for name in "${FORBIDDEN[@]}"; do
  if git ls-files 2>/dev/null | grep -q "$name"; then
    echo "FAIL: tracked file matching *$name*"
    git ls-files | grep "$name" || true
    FAIL=1
  fi
done

echo "==> Scanning for JWT / credential patterns..."
PATTERNS=(
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.'
  'telegram_bot_token.*[0-9]{8,}:'
  'BEGIN (RSA |OPENSSH )?PRIVATE KEY'
)
for pat in "${PATTERNS[@]}"; do
  if grep -rE --include='*.py' --include='*.json' --include='*.yaml' --include='*.md' -l "$pat" custom_components/ docs/ 2>/dev/null; then
    echo "FAIL: pattern match: $pat"
    FAIL=1
  fi
done

echo "==> Checking for __pycache__..."
if find custom_components -type d -name __pycache__ 2>/dev/null | grep -q .; then
  echo "FAIL: __pycache__ present"
  find custom_components -type d -name __pycache__
  FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo "OK: no secrets detected"
else
  exit 1
fi
