#!/usr/bin/env bash
# Publish to https://github.com/SmartEnergyHub/hidro-premierenergy
# Usage: GITHUB_TOKEN=YOUR_GITHUB_TOKEN ./scripts/publish-github.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GIT=/usr/bin/git

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: Set GITHUB_TOKEN (PAT with repo + workflow scopes)"
  echo "  GITHUB_TOKEN=YOUR_GITHUB_TOKEN ./scripts/publish-github.sh"
  exit 1
fi

./scripts/verify-repo-clean.sh
./scripts/lint.sh

$GIT remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/SmartEnergyHub/hidro-premierenergy.git"
$GIT push --force-with-lease origin main
$GIT push --force origin --tags

echo "OK: https://github.com/SmartEnergyHub/hidro-premierenergy"
