# Publish checklist — SmartEnergyHub/hidro-premierenergy

## Security (pre-push) — mandatory

- [ ] `./scripts/verify-repo-clean.sh` passes (includes gitleaks + git history banlist)
- [ ] No real/dev passwords anywhere (including `scripts/secret-scan.sh` regex tests)
- [ ] No `secrets.json`, `token.txt`, `session.json`, `cookies_import.json` in tree
- [ ] No `browser_profile/`, `invoices/`, `logs/`, `backups/`
- [ ] No JWT (`eyJ...`) in source files
- [ ] `.gitignore` covers runtime artifacts

## HACS

- [ ] `hacs.json` at repo root
- [ ] `custom_components/premier_energy/manifest.json`
- [ ] `custom_components/hidroelectrica/manifest.json`
- [ ] Config flow enabled on both

## Release

- Tag after security verification
- Update `CHANGELOG.md`
- Recreate GitHub release if history was rewritten (force push)
