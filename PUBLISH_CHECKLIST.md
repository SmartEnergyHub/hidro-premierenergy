# Publish checklist — johnny29/hidro-premierenergy

## Security (pre-push)

- [x] No `secrets.json`, `token.txt`, `session.json`, `cookies_import.json` in tree
- [x] No `browser_profile/`, `invoices/`, `logs/`, `backups/`
- [x] No JWT (`eyJ...`) in source files
- [x] `./scripts/secret-scan.sh` passes
- [x] `.gitignore` covers runtime artifacts

## HACS

- [x] `hacs.json` at repo root
- [x] `custom_components/premier_energy/manifest.json`
- [x] `custom_components/hidroelectrica/manifest.json`
- [x] Config flow enabled on both

## Release

- Tag: `v1.0.0`
- `CHANGELOG.md` section [1.0.0]
