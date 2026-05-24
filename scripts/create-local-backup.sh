#!/usr/bin/env bash
# Backup local hidro-premierenergy pentru test HACS / rollback.
# Usage: ./scripts/create-local-backup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/../backupuri"
mkdir -p "${OUT}"
ts="$(date +%Y%m%d-%H%M%S)"
ver="$(python3 -c "import json; print(json.load(open('${ROOT}/custom_components/hidroelectrica/manifest.json'))['version'])" 2>/dev/null || echo unknown)"

name_full="hidro-premierenergy-v${ver}-full-${ts}.tar.gz"
name_hacs="hidro-premierenergy-v${ver}-hacs-${ts}.tar.gz"

cd "${ROOT}"
# Arhivă completă (inclusiv .git, docs, scripts)
tar -czf "${OUT}/${name_full}" \
  --exclude='./__pycache__' \
  --exclude='**/__pycache__' \
  --exclude='**/*.pyc' \
  .

# Doar ce instalează HACS (+ hacs.json, README pentru UI)
tar -czf "${OUT}/${name_hacs}" \
  hacs.json README.md LICENSE CHANGELOG.md \
  custom_components/premier_energy \
  custom_components/hidroelectrica

ls -lh "${OUT}/${name_full}" "${OUT}/${name_hacs}"
echo ""
echo "HACS custom repo URL: https://github.com/SmartEnergyHub/hidro-premierenergy"
echo "Ghid test: docs/HACS_INSTALL.md"
