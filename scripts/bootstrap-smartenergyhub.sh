#!/usr/bin/env bash
# Bootstrap SmartEnergyHub/hidro-premierenergy — run AFTER empty repo exists on GitHub.
# Requires GITHUB_TOKEN with Contents: Read/Write + Workflows: Read/Write on the repo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GIT=/usr/bin/git
ORG=SmartEnergyHub
REPO=hidro-premierenergy
API="https://api.github.com/repos/${ORG}/${REPO}"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: export GITHUB_TOKEN first (do not commit or log it)"
  exit 1
fi

echo "==> Security scan..."
./scripts/verify-repo-clean.sh
./scripts/lint.sh

echo "==> Checking remote repository exists..."
HTTP=$(curl -sS -o /tmp/repo_check.json -w '%{http_code}' \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "$API")
if [ "$HTTP" != "200" ]; then
  echo "FAIL: ${ORG}/${REPO} not found (HTTP $HTTP)"
  echo "Create empty repo on GitHub first:"
  echo "  https://github.com/organizations/${ORG}/repositories/new"
  echo "  Name: ${REPO} | Public | Issues + Discussions enabled"
  echo "Then grant this PAT access to the repository (Contents + Workflows)."
  exit 1
fi

echo "==> Enable Discussions + HACS repo metadata..."
curl -sS -X PATCH \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${ORG}/${REPO}" \
  -d '{"has_discussions":true,"description":"Home Assistant FULL AUTO — Premier Energy (gaze naturale) + Hidroelectrica (energie electrică). HACS custom integrations for Romania.","topics":["homeassistant","hacs-integration","integration","romania","energy","utility"]}' >/dev/null

echo "==> Push main + tags..."
$GIT remote remove origin 2>/dev/null || true
$GIT remote add origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${ORG}/${REPO}.git"
$GIT push --force origin main
$GIT push --force origin --tags
$GIT remote set-url origin "https://github.com/${ORG}/${REPO}.git"

echo "==> Done: https://github.com/${ORG}/${REPO}"
echo "Release workflow will create notes for pushed tags (v1.1.1, etc.)"
