# Scripturi legacy Premier (shell_command + Telegram)

Pe **Home Assistant OS**, comenzile Telegram rulează `shell_command` **în containerul** `homeassistant`, unde Chromium/Selenium eșuează adesea. Soluția:

1. **Refresh token pe HOST** via SSH (`172.30.32.1`)
2. **Scripturi Python** care apelează API Premier din container (token proaspăt)
3. **Cron pe host** la 4h pentru refresh preventiv

## Instalare rapidă

```bash
# Pe HA (SSH / Terminal add-on)
mkdir -p /config/premier_energy/facturi
python3 -m venv /config/premier_energy/venv
/config/premier_energy/venv/bin/pip install requests selenium

# Copiază din repo (examples/legacy/):
#   premier_session.py → send_index.py → send_last_invoice_telegram.py
#   refresh_token_simple.py
cp premier_secrets.json.example /config/premier_energy/secrets.json
# Editează secrets.json (email, password, Telegram — NU comite în git)

# SSH container → host (o dată)
./scripts/setup-ha-premier-host-ssh.sh
```

## Fișiere

| Fișier | Destinație HA |
|--------|----------------|
| `premier_session.py` | `/config/premier_energy/premier_session.py` |
| `premier_refresh_token_simple.py` | `/config/premier_energy/refresh_token_simple.py` |
| `premier_send_index.py` | `/config/premier_energy/send_index.py` |
| `premier_send_last_invoice_telegram.py` | `/config/premier_energy/send_last_invoice_telegram.py` |
| `configuration_shell_commands.example.yaml` | fragment în `configuration.yaml` |
| `telegram_commands.yaml` (energie/) | `packages/energie/` |

## Test

```bash
# Pe HOST (SSH)
/config/premier_energy/venv/bin/python3 /config/premier_energy/refresh_token_simple.py

# Din container (ca Telegram)
docker exec homeassistant /config/premier_energy/venv/bin/python3 /config/premier_energy/send_last_invoice_telegram.py
```

## Integrare HACS (alternativă)

Serviciile `premier_energy.send_index` și `send_last_invoice_telegram` folosesc același mecanism SSH→host în v1.1.4+. Pentru Telegram pe HA OS, **shell_command rămâne recomandat** (vezi `examples/energie/telegram_commands.yaml`).
