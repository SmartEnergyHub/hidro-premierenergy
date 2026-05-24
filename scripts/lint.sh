#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
command -v ruff >/dev/null || pip install -q ruff
ruff check custom_components/
ruff format --check custom_components/
python3 -m compileall -q custom_components/
find custom_components -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
./scripts/secret-scan.sh
echo "Lint OK"
