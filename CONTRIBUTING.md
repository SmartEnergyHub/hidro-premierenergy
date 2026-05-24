# Contributing

Thank you for contributing to HA Energie Romania integrations.

## Development setup

```bash
git clone https://github.com/SmartEnergyHub/hidro-premierenergy.git
cd hidro-premierenergy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Copy `custom_components/` into a Home Assistant `config` directory for live testing.

## Pull requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-change`
3. Run checks locally: `./scripts/lint.sh`
4. Commit with clear messages (see existing history)
5. Open a PR against `main`

## Code style

- Python 3.11+ syntax where compatible with HA 2024.12+
- `ruff` for lint/format
- Type hints encouraged on public APIs
- Selenium/browser code stays in `lib/` and runs only via executor

## Translations

Edit `strings.json` and mirror changes in `translations/en.json` and `translations/ro.json`.

## No secrets in PRs

PRs containing tokens, cookies, passwords, or real `browser_profile/` data will be rejected.
