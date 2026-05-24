# Release checklist

## Pre-release

- [ ] `./scripts/lint.sh` passes locally
- [ ] `./scripts/secret-scan.sh` passes
- [ ] Version bumped in both `manifest.json` files
- [ ] `CHANGELOG.md` updated with date
- [ ] No `__pycache__`, secrets, or browser profiles in tree

## Tag & release

```bash
git tag -a v1.0.0 -m "Release v1.0.0 — initial public release"
git push origin main
git push origin v1.0.0
```

GitHub Actions `release.yml` creates the GitHub Release from `CHANGELOG.md`.

## Post-release HACS

1. Submit repo to [HACS default](https://github.com/hacs/default) (optional, for default catalog)
2. Or share as **Custom repository** — users add URL directly
3. Verify HACS shows both integrations after download

## First-time GitHub repo

```bash
# Create repo on GitHub (empty, no README)
git remote add origin https://github.com/ha-energie-romania/ha-energie-integrations.git
git push -u origin main
git push origin v1.0.0
```

Repository: `https://github.com/SmartEnergyHub/hidro-premierenergy`
