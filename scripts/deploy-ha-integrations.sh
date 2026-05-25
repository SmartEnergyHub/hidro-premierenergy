#!/usr/bin/env bash
# Deploy ambele integrări + pachete Telegram index pe Home Assistant (fără restart complet).
# Usage:
#   HA_SSH_PASS='***' ./scripts/deploy-ha-integrations.sh
#   HA_SSH='root@moi-cab.dyndns.tv' HA_SSH_PORT=2233 ./scripts/deploy-ha-integrations.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HA_SSH="${HA_SSH:-root@moi-cab.dyndns.tv}"
HA_SSH_PORT="${HA_SSH_PORT:-2233}"

RSYNC_SSH="ssh -p ${HA_SSH_PORT} -o StrictHostKeyChecking=no"
if [ -n "${HA_SSH_PASS:-}" ]; then
  command -v sshpass >/dev/null || { echo "Instalează sshpass"; exit 1; }
  RSYNC_SSH="sshpass -p ${HA_SSH_PASS} ssh -p ${HA_SSH_PORT} -o StrictHostKeyChecking=no"
fi

for comp in hidroelectrica premier_energy; do
  echo "==> ${comp}"
  rsync -avz --delete -e "${RSYNC_SSH}" \
    "${ROOT}/custom_components/${comp}/" \
    "${HA_SSH}:/config/custom_components/${comp}/"
done

echo "==> telegram_index_commands.yaml"
ssh_cmd=(ssh -p "${HA_SSH_PORT}" -o StrictHostKeyChecking=no)
if [ -n "${HA_SSH_PASS:-}" ]; then
  ssh_cmd=(sshpass -p "${HA_SSH_PASS}" ssh -p "${HA_SSH_PORT}" -o StrictHostKeyChecking=no)
fi
"${ssh_cmd[@]}" "${HA_SSH}" "mkdir -p /config/packages/energie"
rsync -avz -e "${RSYNC_SSH}" \
  "${ROOT}/examples/energie/telegram_index_commands.yaml" \
  "${HA_SSH}:/config/packages/energie/telegram_index_commands.yaml"

echo "==> Reload YAML (fără ha core restart)"
"${ssh_cmd[@]}" "${HA_SSH}" \
  'ha core reload 2>/dev/null || echo "Reload manual: Automations + Scripts din Developer Tools"'

echo "==> Gata. Test: /indexhidro și /indexgaze în Telegram."
