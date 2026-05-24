# Migration from shell_command setup

## Before (legacy)

- `/config/premier_energy/` scripts + YAML packages
- `/config/hidroelectrica/` scripts + YAML packages
- Manual `secrets.json`, optional `cookies_import.json`

## After (custom component)

1. Install integration via HACS or manual copy
2. Add integration in UI — enter credentials once
3. Disable legacy automations (optional, can run parallel during test):

```yaml
# Comment out in packages/energie/:
# - premier_refresh_token_schedule
# - hidro_session_manager_schedule
```

4. Legacy Telegram commands in `automations.yaml` can call new services:

```yaml
action: hidroelectrica.download_invoice
data:
  invoice_number: "{{ ... }}"
```

## Parallel operation

Both setups can coexist. Custom component uses separate storage:
- `/config/premier_energy/<entry_id>/`
- `/config/hidroelectrica/<entry_id>/`

Legacy paths `/config/premier_energy/token.txt` are NOT overwritten.

## Rollback

1. Remove integration from HA UI
2. Re-enable YAML package automations
3. Legacy scripts remain in `/config/premier_energy/` and `/config/hidroelectrica/`
