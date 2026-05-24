# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.1.0] - 2026-05-24

### Added
- **Support Development** — butoane, servicii, Options Flow, donate via [hidro-premierenergy.ro/donate](https://hidro-premierenergy.ro/donate)
- Export **Support Bundle** ZIP redactat (fără parole/tokenuri/cookies)
- Servicii: `open_support_link`, `export_support_bundle`, `report_issue`
- GitHub: FUNDING.yml, SUPPORT.md, issue templates, Discussions links
- Telemetrie anonimă **opt-in** (Options Flow)

### Fixed
- **Hidroelectrica cookies:** director sesiune unificat `/config/hidroelectrica/`, detectare login page, auto-login prioritar
- Health/token oglindite pentru compatibilitate legacy

## [1.0.2] - 2026-05-24

### Fixed
- **Premier Energy (gaze naturale):** refresh proactiv token când expiră în <20 min
- Refresh automat la 90s după pornirea HA (`homeassistant_started`)
- Oglindire `token.txt` + `health.json` în `/config/premier_energy/` (compatibilitate legacy)
- Documentat fix `shell_command.premier_health_check` — [examples/legacy/premier_shell_command.yaml](examples/legacy/premier_shell_command.yaml)

## [1.0.1] - 2026-05-24

### Added
- **docs/INSTALLATION.md** — ghid complet instalare (dependențe, pași, verificări SSH)
- **examples/lovelace_premier_energy.yaml** — card Lovelace Premier Energy (gaze naturale)
- **examples/lovelace_hidroelectrica.yaml** — card Lovelace Hidroelectrica (energie electrică)

### Changed
- README rescris: dependențe, pași instalare, link-uri documentație
- Denumiri integrări: **Premier Energy (gaze naturale)**, **Hidroelectrica (energie electrică)**
- `dashboard_energie.yaml` actualizat cu exemple combinate

## [1.0.0] - 2026-05-24

### Added

#### Premier Energy (`premier_energy`)
- Config Flow — email + password only
- Azure B2C auto-login via Selenium + persistent browser profile
- JWT token refresh every 10 minutes (skip browser when token valid)
- Sensors: invoice amount/number, due date, consumption m³/MWh, address
- Binary sensor: connectivity
- Buttons: refresh session, force login
- Services: `refresh_session`, `force_login`, `download_invoice`, `send_index`, `export_debug`
- Diagnostics with credential redaction

#### Hidroelectrica (`hidroelectrica`)
- Config Flow — username + password (+ optional Telegram)
- FULL AUTO session: keepalive + Xvfb headed login (reCAPTCHA v3)
- Coordinator polling every 5 minutes
- Sensors: invoice, POD, balance, index, consumption
- Binary sensors: session OK, self-reading period
- PDF download service
- Legacy portal API preserved (`hidro_api`, `session`, `api_client`)

#### Repository
- HACS-ready monorepo with both integrations
- GitHub Actions: hassfest, HACS validate, ruff, secret scan
- Blueprint: invoice change notification
- Example Lovelace dashboard
- Documentation: architecture, auth flows, migration, security, limitations

### Security
- No credentials in repository
- Config Entry storage for user passwords
- Diagnostics redact tokens and passwords

### Migration
- Legacy shell_command setup can run in parallel — see [docs/MIGRATION.md](docs/MIGRATION.md)

[1.0.0]: https://github.com/johnny29/hidro-premierenergy/releases/tag/v1.0.0
