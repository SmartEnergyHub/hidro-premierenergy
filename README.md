# HA Energie Romania

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/johnny29/hidro-premierenergy)](https://github.com/johnny29/hidro-premierenergy/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Custom Home Assistant integrations for Romanian utility portals — **FULL AUTO**, production-ready.

| Integration | Provider | Auth |
|-------------|----------|------|
| **premier_energy** | Premier Energy (gaze) | Azure B2C JWT |
| **hidroelectrica** | Hidroelectrica (electricitate) | iHidro + reCAPTCHA |

> Enter **email/password** or **username/password** once. No cookies, tokens, F12, or manual YAML.

---

## Features

### Both integrations
- Config Flow UI (no YAML editing)
- Auto-login & auto-refresh
- Self-healing with retry + watchdog
- Recovery after HA reboot
- Diagnostics (secrets redacted)
- Services: refresh, force login, PDF, debug export

### Premier Energy
- Invoice amount, number, due date
- Gas consumption (m³ / MWh)
- Address & reading period
- JWT refresh every 10 min

### Hidroelectrica
- Invoice, POD, balance, meter index
- Self-reading period sensor
- Session keepalive every 5 min
- Xvfb + headed Chromium for reCAPTCHA

---

## Compatibility

| Component | Minimum |
|-----------|---------|
| Home Assistant | 2024.12.0 |
| HACS | 1.34.0 |
| Python | 3.11+ (HA bundled) |
| Chromium | `/usr/bin/chromium` |
| ChromeDriver | `/usr/bin/chromedriver` |
| Xvfb | `/usr/bin/Xvfb` (Hidro only) |

| Platform | Supported |
|----------|-----------|
| Home Assistant OS | ✅ Recommended |
| Supervised | ✅ |
| Container | ⚠️ Requires Chromium/Xvfb in container |
| Core (venv) | ⚠️ Manual Chromium setup |

| Architecture | Supported |
|--------------|-----------|
| Raspberry Pi (ARM) | ✅ |
| x86-64 | ✅ |

---

## Installation

### HACS (recommended)

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. URL: `https://github.com/johnny29/hidro-premierenergy`
3. Category: **Integration**
4. **Download**
5. **Restart Home Assistant**
6. **Settings** → **Devices & Services** → **Add Integration**
7. Search **Premier Energy** or **Hidroelectrica**

### Manual

```bash
cd /config
git clone https://github.com/johnny29/hidro-premierenergy.git /tmp/ha-energie
cp -r /tmp/ha-energie/custom_components/premier_energy custom_components/
cp -r /tmp/ha-energie/custom_components/hidroelectrica custom_components/
# Restart Home Assistant
```

---

## Quick start

### Premier Energy
1. Add integration → enter **email** + **password** from [my.premierenergy.ro](https://my.premierenergy.ro)
2. Entities appear under device **Premier Energy**

### Hidroelectrica
1. Add integration → enter **username** + **password** from [ihidro.ro](https://ihidro.ro/portal/)
2. Optional: Telegram bot token + chat ID for legacy notifications
3. Entities appear under device **Hidroelectrica**

---

## Example dashboard

See [examples/dashboard_energie.yaml](examples/dashboard_energie.yaml) — vertical stack with invoice sensors, connectivity, refresh buttons.

```
┌─────────────────────────────────┐
│ Premier Energy (Gaze)           │
│  Factură: 330.92 RON            │
│  Scadență: 18/06/2026           │
│  ● Conectat                     │
│  [ Reîmprospătează sesiunea ]   │
├─────────────────────────────────┤
│ Hidroelectrica (Electricitate)  │
│  Factură: 887.2 RON             │
│  POD: 8000244846                │
│  ● Sesiune OK                   │
│  [ Re-login forțat ]            │
└─────────────────────────────────┘
```

---

## Services

| Service | Description |
|---------|-------------|
| `premier_energy.refresh_session` | Refresh JWT / data |
| `premier_energy.force_login` | Force Azure B2C login |
| `premier_energy.download_invoice` | Download PDF |
| `hidroelectrica.refresh_session` | Keepalive + fetch |
| `hidroelectrica.force_login` | Xvfb auto-login |
| `hidroelectrica.download_invoice` | Download PDF |
| `*.export_debug` | Log debug info (redacted) |

Examples: [examples/services.yaml](examples/services.yaml)

---

## Architecture

```
Config Flow (credentials)
        ↓
DataUpdateCoordinator (async)
        ↓
Executor → AuthManager / SessionManager
        ↓
API → Sensors / Binary sensors / Buttons
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [Auth flows](docs/AUTH_FLOWS.md)

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `invalid_auth` at setup | Verify portal credentials in browser |
| Hidro captcha fail | Ensure Xvfb: `ls /usr/bin/Xvfb` |
| Chromium lock timeout | Wait 3 min; check stuck processes |
| Stale data | Press **Refresh session** button |

Full guide: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) · [FAQ](docs/FAQ.md)

---

## Migration from shell_command

Legacy scripts in `/config/premier_energy/` and `/config/hidroelectrica/` can run in parallel during testing.

[docs/MIGRATION.md](docs/MIGRATION.md)

---

## Security

- Credentials encrypted by Home Assistant Config Entries
- No secrets in this repository
- Diagnostics redact passwords/tokens

[SECURITY.md](SECURITY.md) · [docs/SECURITY.md](docs/SECURITY.md)

---

## Known limitations

[docs/LIMITATIONS.md](docs/LIMITATIONS.md)

---

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

[MIT](LICENSE) © HA Energie Romania Contributors
