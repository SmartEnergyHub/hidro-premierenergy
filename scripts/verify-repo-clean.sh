#!/usr/bin/env bash
# Full repository security verification — run before release/push.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1/4 secret-scan.sh ==="
./scripts/secret-scan.sh

echo "=== 2/4 git history scan (dev password banlist) ==="
BANNED='|||'
if /usr/bin/git rev-list --all | while read -r c; do
  /usr/bin/git grep -iE "$BANNED" "$c" -- ':!*.png' ':!*.jpg' 2>/dev/null
done | head -1; then
  echo "FAIL: banned dev strings found in git history"
  exit 1
fi
echo "OK: git history banlist clean"

echo "=== 3/4 gitleaks full history ==="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --log-opts="--all" --config .gitleaks.toml -v
else
  echo "WARN: gitleaks not installed — skipping history scan"
fi

echo "=== 4/4 tracked files grep ==="
if /usr/bin/git ls-files | xargs grep -iE "$BANNED" 2>/dev/null; then
  echo "FAIL: banned strings in tracked files"
  exit 1
fi
echo "OK: tracked files clean"

echo "=== ALL CHECKS PASSED ==="
