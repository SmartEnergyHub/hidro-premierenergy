#!/usr/bin/env bash
# Deploy integrări + exemple Telegram pe Home Assistant (fără restart complet).
# Usage:
#   HA_SSH='root@YOUR_HA_HOST' HA_SSH_PORT=22 ./scripts/deploy-ha-integrations.sh
#   HA_SSH_PASS='***' HA_SSH='root@YOUR_HA_HOST' ./scripts/deploy-ha-integrations.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HA_SSH="${HA_SSH:?Set HA_SSH=root@YOUR_HA_HOST}"
HA_SSH_PORT="${HA_SSH_PORT:-22}"

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

echo "==> telegram_commands.yaml + legacy Premier scripts"
ssh_cmd=(ssh -p "${HA_SSH_PORT}" -o StrictHostKeyChecking=no)
if [ -n "${HA_SSH_PASS:-}" ]; then
  ssh_cmd=(sshpass -p "${HA_SSH_PASS}" ssh -p "${HA_SSH_PORT}" -o StrictHostKeyChecking=no)
fi
"${ssh_cmd[@]}" "${HA_SSH}" "mkdir -p /config/packages/energie /config/premier_energy"
rsync -avz -e "${RSYNC_SSH}" \
  "${ROOT}/examples/energie/telegram_commands.yaml" \
  "${HA_SSH}:/config/packages/energie/telegram_commands.yaml"
for src dest in \
  premier_session.py premier_session.py \
  premier_refresh_token_simple.py refresh_token_simple.py \
  premier_send_index.py send_index.py \
  premier_send_last_invoice_telegram.py send_last_invoice_telegram.py; do
  rsync -avz -e "${RSYNC_SSH}" "${ROOT}/examples/legacy/${src}" "${HA_SSH}:/config/premier_energy/${dest}"
done

echo "==> Reload YAML (fără ha core restart)"
"${ssh_cmd[@]}" "${HA_SSH}" \
  'ha core reload 2>/dev/null || echo "Reload manual: Developer Tools → YAML → Reload all YAML"'

echo "==> Gata. Înlocuiește YOUR_TELEGRAM_CONFIG_ENTRY_ID în telegram_commands.yaml, apoi testează /facturagaze și /indexgaze 12345"
