# Security Notes

- Credentials entered via HA Config Flow are stored encrypted by Home Assistant core
- Never commit `secrets.json`, `token.txt`, `session.json` to git
- Diagnostics automatically redact sensitive fields
- Browser profiles may contain session cookies — stored under `/config/<domain>/<entry_id>/`
- Telegram tokens optional in Hidro config flow — stored in config entry
- Recommend dedicated portal password + 2FA on provider side if available
- Lock file `/config/.chromium_automation.lock` prevents concurrent browser abuse
