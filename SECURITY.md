# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| 1.1.x   | Yes       |

## Reporting a vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.

1. Open a [private security advisory](https://github.com/johnny29/hidro-premierenergy/security/advisories/new) on GitHub, or
2. Contact maintainers via GitHub (see `CODEOWNERS`).

Include: affected integration, steps to reproduce, impact assessment.

## What we store

- **Credentials** (email/password or username/password): Home Assistant Config Entry encryption at rest.
- **Tokens / cookies / CSRF**: under `/config/<domain>/` on the user's HA instance only — **never** in this repository.

## Repository hygiene (maintainers & contributors)

- **Never commit** real passwords, test passwords used in development, tokens, cookies, JWTs, Telegram IDs, or examples derived from real data — even in scan scripts, regex tests, or placeholders.
- Use only generic placeholders in docs/examples: `your_password_here`, `example_password`, `dummy_value`, `test_token_example`.
- Run `./scripts/verify-repo-clean.sh` before every push.
- CI runs gitleaks + custom secret scan on full git history.

## User responsibilities

- Use strong, unique passwords for utility portals.
- Restrict file permissions on `/config/` (HA default).
- Do not share diagnostics exports publicly without reviewing redacted fields.
- Review [docs/SECURITY.md](docs/SECURITY.md) for technical details.

## Automated checks

This repository runs secret scanning in CI before merge. Never commit `secrets.json`, `token.txt`, `session.json`, or browser profiles.
