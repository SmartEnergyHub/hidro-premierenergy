#!/usr/bin/env bash
# Configurează SSH din containerul homeassistant către HOST (Chromium refresh Premier).
# Rulează pe HA OS ca root (SSH sau Terminal add-on).
set -euo pipefail

SSH_DIR="/config/.ssh"
KEY="${SSH_DIR}/ha_to_host"
HOST="172.30.32.1"

mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

if [ ! -f "${KEY}" ]; then
  ssh-keygen -t ed25519 -N "" -f "${KEY}" -q
  cat "${KEY}.pub" >> /root/.ssh/authorized_keys
  echo "Cheie SSH generată: ${KEY}"
fi
touch "${SSH_DIR}/known_hosts"
chmod 600 "${KEY}" "${SSH_DIR}/known_hosts" 2>/dev/null || true

docker exec homeassistant apk add --no-cache openssh-client 2>/dev/null || true

if docker exec homeassistant ssh -i "${KEY}" -o StrictHostKeyChecking=no \
  -o "UserKnownHostsFile=${SSH_DIR}/known_hosts" "root@${HOST}" "echo SSH_OK"; then
  echo "OK: container → host SSH funcțional"
else
  echo "FAIL: verifică că rulezi ca root pe HA OS și hostul ${HOST} răspunde"
  exit 1
fi

# Cron refresh token pe HOST (opțional, recomandat)
CRON_LINE="0 */4 * * * /config/premier_energy/venv/bin/python3 /config/premier_energy/refresh_token_simple.py >> /config/premier_energy/refresh.log 2>&1"
( crontab -l 2>/dev/null | grep -v refresh_token_simple || true
  echo "${CRON_LINE}"
) | crontab -
echo "Cron refresh token la 4h instalat pe host."
