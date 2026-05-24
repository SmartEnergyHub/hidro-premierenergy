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

- Verify email/password at https://my.premierenergy.ro
- Check logs: `/config/premier_energy/<entry_id>/` or HA → Settings → System → Logs
- Ensure Chromium + chromedriver exist: `which chromium chromedriver`

## Hidro — "invalid_auth" at setup

- Verify credentials at https://ihidro.ro/portal/
- Xvfb required: `which Xvfb` → `/usr/bin/Xvfb`
- Check reCAPTCHA errors in logs — headed browser must work (not headless)

## Session keeps failing

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
