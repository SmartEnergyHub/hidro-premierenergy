# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

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
