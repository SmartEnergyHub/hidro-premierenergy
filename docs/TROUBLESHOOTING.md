# Troubleshooting

## Telegram — `/facturagaze` sau `/indexgaze` nu răspunde

**Cauză (HA OS):** `shell_command` și serviciile integrării rulează în **containerul** `homeassistant`. Chromium/Selenium eșuează acolo (`DevToolsActivePort`, `session not created`) → token JWT expirat → comanda pare să „nu facă nimic”.

**Verificare:**

```bash
docker exec homeassistant /config/premier_energy/venv/bin/python3 /config/premier_energy/refresh_token_simple.py
# Eșec aici = normal în container

ssh root@localhost /config/premier_energy/venv/bin/python3 /config/premier_energy/refresh_token_simple.py
# Succes TOKEN_OK = Chromium funcționează pe HOST
```

**Fix (v1.1.4+):**

1. Rulează o dată: `scripts/setup-ha-premier-host-ssh.sh` (SSH container → host `172.30.32.1`)
2. Copiază scripturile din `examples/legacy/` în `/config/premier_energy/`
3. Completează `/config/premier_energy/secrets.json` (vezi `premier_secrets.json.example`)
4. Folosește `examples/energie/telegram_commands.yaml` (mesaj „⏳ Procesez...” + shell_command)
5. Index: **`/indexhidro 23750`** și **`/indexgaze 12345`** — cifra trebuie în comandă

Integrarea HACS folosește același refresh SSH→host în `auth_manager.refresh_token()`.

## Premier — token expirat după restart HA

**Cauză (setup legacy YAML):** `shell_command.premier_health_check` definit doar în `packages/` — HA nu înregistrează serviciul → watchdog-ul eșuează → tokenul nu se reînnoiește.

**Fix:**

1. Mută comenzile în **`configuration.yaml`** (vezi [examples/legacy/premier_shell_command.yaml](../examples/legacy/premier_shell_command.yaml))
2. Elimină blocul `shell_command:` duplicat din pachetul YAML
3. Restart HA

**Cu integrarea HACS `premier_energy` (v1.0.2+):**

- Refresh automat la 10 min + la 90s după pornirea HA
- Token/health oglindite în `/config/premier_energy/token.txt` și `health.json` pentru carduri legacy

## Premier — "invalid_auth" at setup

**Cauză frecventă (HA OS):** Chromium există pe **host** (`which chromium` în SSH), dar integrarea rulează în **containerul** `homeassistant`, unde `/usr/bin/chromium` lipsește. Mesajul generic `invalid_auth` apare chiar dacă email/parola sunt corecte.

**Verificare:**

```bash
docker exec homeassistant sh -c 'ls /usr/bin/chromium /usr/bin/chromedriver'
```

**Fix (o dată; se pierde la update major HA Core — vezi mai jos):**

```bash
docker exec homeassistant apk add --no-cache chromium chromium-chromedriver xvfb
```

Apoi reîncearcă **Setări → Integrări → Adaugă integrare → Premier Energy**.

**Persistență după update HA:** vezi [examples/legacy/browser_deps_bootstrap.yaml](../examples/legacy/browser_deps_bootstrap.yaml) (automation la pornire).

**Dacă Chromium e instalat dar tot eșuează:**

- Verify email/password at https://my.premierenergy.ro
- Check logs: `/config/premier_energy/<entry_id>/` or HA → Settings → System → Logs

## Hidro — "invalid_auth" at setup

**Aceeași cauză ca la Premier** — Chromium trebuie în containerul `homeassistant`, nu doar pe host:

```bash
docker exec homeassistant apk add --no-cache chromium chromium-chromedriver xvfb
```

- Verify credentials at https://ihidro.ro/portal/
- Xvfb required inside container: `docker exec homeassistant which Xvfb`
- Check reCAPTCHA errors in logs — headed browser must work (not headless)

## Session keeps failing (Hidroelectrica)

**Mesaj legacy** „Reimportă cookies / import_session.py” vine de la scripturile vechi din `/config/hidroelectrica/` sau pachetul YAML legacy — **nu** de la integrarea HACS v1.1.2+.

### Fix rapid (integrare HACS)

1. **Setări → Integrări → Hidroelectrica → Re-login forțat** (buton)  
   sau serviciu: `hidroelectrica.force_login`
2. Așteaptă ~2 min (Xvfb + reCAPTCHA + Chromium)
3. Verifică `binary_sensor.*_sesiune_ok` → ON

### După restart HA

Integrarea v1.1.2+ face recovery automat la **90s** după pornire. Dacă eșuează, apasă Re-login forțat.

### Dezactivează conflictul legacy

Dacă ai încă `/config/packages/energie/hidroelectrica.yaml` cu `shell_command.hidro_*` la 30 min, **dezactivează** automatizările legacy (integrarea HACS le înlocuiește). Altfel primești notificări Telegram vechi cu `import_session.py`.

### Cale sesiune (obligatoriu)

Toate fișierele sesiune: **`/config/hidroelectrica/session.json`** (nu sub `<entry_id>/`).

## Session keeps failing (general)

1. Press **Force login** button entity
2. Call service `*.force_login`
3. Check diagnostics: Settings → Integrations → Configure → Download diagnostics

## Chromium lock timeout

Premier and Hidro share lock. Wait 3 min or check stuck processes:

```bash
pgrep -a chromium
```

## Debug export

```yaml
service: premier_energy.export_debug
service: hidroelectrica.export_debug
```

## Logs

```bash
grep -i premier /config/home-assistant.log
grep -i hidro /config/home-assistant.log
```
