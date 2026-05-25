#!/usr/bin/env bash
# Deploy Hidroelectrica custom component to Home Assistant via rsync+SSH.
# Usage: HA_SSH='root@host' HA_SSH_PORT=2233 ./scripts/deploy-ha-hidro.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/custom_components/hidroelectrica"
HA_SSH="${HA_SSH:?Set HA_SSH=root@YOUR_HA_HOST}"
HA_SSH_PORT="${HA_SSH_PORT:-22}"
DEST="/config/custom_components/hidroelectrica"

RSYNC_SSH="ssh -p ${HA_SSH_PORT} -o StrictHostKeyChecking=no"
if [ -n "${HA_SSH_PASS:-}" ]; then
  RSYNC_SSH="sshpass -p ${HA_SSH_PASS} ssh -p ${HA_SSH_PORT} -o StrictHostKeyChecking=no"
fi

echo "==> Deploy ${SRC} -> ${HA_SSH}:${DEST}"
rsync -avz --delete -e "${RSYNC_SSH}" "${SRC}/" "${HA_SSH}:${DEST}/"

echo "==> Sync lib/session fixes to legacy path (dacă există)"
rsync -avz -e "${RSYNC_SSH}" \
  "${SRC}/lib/session.py" "${SRC}/lib/ha_session.py" "${SRC}/lib/api_client.py" \
  "${HA_SSH}:/config/hidroelectrica/lib/" 2>/dev/null || true

echo "==> Done. În HA: Repornește integrarea Hidroelectrica sau Re-login forțat."
echo "    Serviciu: hidroelectrica.force_login"
