# Security Notes

- Credentials entered via HA Config Flow are stored encrypted by Home Assistant core
- Never commit `secrets.json`, `token.txt`, `session.json` to git
- Diagnostics automatically redact sensitive fields
- Browser profiles may contain session cookies — stored under `/config/<domain>/`
- Telegram tokens optional in Hidro config flow — stored in config entry
- Recommend dedicated portal password + 2FA on provider side if available
- Lock file `/config/.chromium_automation.lock` prevents concurrent browser abuse

## Examples and documentation

Use **only generic placeholders** in README, docs, issue templates, and test fixtures:

| Field | Placeholder |
|-------|-------------|
| Password | `your_password_here` |
| Username | `your_username_here` |
| Email | `user@example.com` |
| Telegram bot token | `test_token_example` |
| Telegram chat ID | `dummy_value` |

Never use passwords or usernames from development, staging, or production systems — even as “test” values in secret scanners.

## Pre-push verification

```bash
./scripts/verify-repo-clean.sh
```
