# Troubleshooting

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
