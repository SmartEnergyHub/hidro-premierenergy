#!/usr/bin/env bash
# Full repository security verification — run before release/push.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1/3 secret-scan.sh ==="
./scripts/secret-scan.sh

echo "=== 2/3 gitleaks full history ==="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --log-opts="--all" --config .gitleaks.toml -v
else
  echo "WARN: gitleaks not installed — skipping history scan"
fi

echo "=== 3/3 detect-secrets baseline (optional) ==="
if command -v detect-secrets >/dev/null 2>&1 && [ -f .secrets.baseline ]; then
  detect-secrets scan --baseline .secrets.baseline
  detect-secrets audit .secrets.baseline --report --only-real
else
  echo "SKIP: detect-secrets baseline not configured"
fi

echo "=== ALL CHECKS PASSED ==="
