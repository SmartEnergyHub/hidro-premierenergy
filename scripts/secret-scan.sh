#!/usr/bin/env bash
# Fail if secrets or runtime artifacts are tracked.
# IMPORTANT: Never embed real or dev passwords in this file — only generic patterns.
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
  if git ls-files 2>/dev/null | grep -E "(^|/)${name}$" | grep -q .; then
    echo "FAIL: tracked file matching *$name*"
    git ls-files | grep "$name" || true
    FAIL=1
  fi
done

echo "==> Scanning for credential patterns (generic only)..."
SCAN_DIRS=(custom_components docs examples scripts .github)
PATTERNS=(
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.'
  'telegram_bot_token.*[0-9]{8,}:'
  '[0-9]{8,}:[A-Za-z0-9_-]{20,}'
  'BEGIN (RSA |OPENSSH )?PRIVATE KEY'
  'ghp_[A-Za-z0-9]{20,}'
  'github_pat_[A-Za-z0-9_]{20,}'
)
for pat in "${PATTERNS[@]}"; do
  if grep -rE --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' \
    --include='*.md' --include='*.sh' -l "$pat" "${SCAN_DIRS[@]}" 2>/dev/null; then
    echo "FAIL: pattern match: $pat"
    FAIL=1
  fi
done

echo "==> Checking for hardcoded password values in examples..."
# Only scan docs/examples — translation labels use key "password" with UI text, not secrets
PLACEHOLDER_RE='your_password_here|example_password|dummy_value|test_token_example|<PASSWORD>|\*\*\*|\$\{'
if grep -rE --include='*.json' --include='*.yaml' --include='*.yml' \
  "\"password\"[[:space:]]*:[[:space:]]*\"[^\"]+\"" docs examples 2>/dev/null \
  | grep -vEi "$PLACEHOLDER_RE"; then
  echo "FAIL: hardcoded password value in docs/examples (use placeholders only)"
  FAIL=1
fi

echo "==> Checking for __pycache__..."
if find custom_components -type d -name __pycache__ 2>/dev/null | grep -q .; then
  echo "FAIL: __pycache__ present"
  find custom_components -type d -name __pycache__
  FAIL=1
fi

echo "==> Optional gitleaks scan..."
if command -v gitleaks >/dev/null 2>&1; then
  if [ -f .gitleaks.toml ]; then
    gitleaks detect --source . --no-git --config .gitleaks.toml -v || FAIL=1
  else
    gitleaks detect --source . --no-git -v || FAIL=1
  fi
fi

if [ "$FAIL" -eq 0 ]; then
  echo "OK: no secrets detected"
else
  exit 1
fi
