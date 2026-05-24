# Architecture Overview

## Components

### `custom_components/premier_energy/`

| Module | Role |
|--------|------|
| `config_flow.py` | UI login — email + password |
| `coordinator.py` | `DataUpdateCoordinator` — polling 10 min |
| `lib/auth_manager.py` | Selenium Azure B2C, JWT refresh |
| `lib/api_client.py` | REST API Premier portal |
| `lib/storage.py` | HA Store + browser profile paths |
| `sensor.py` | Invoice, consumption, address |
| `binary_sensor.py` | Connectivity |
| `button.py` | Manual refresh / force login |
| `diagnostics.py` | Redacted debug export |

### `custom_components/hidroelectrica/`

| Module | Role |
|--------|------|
| `config_flow.py` | UI login — username + password |
| `coordinator.py` | Polling 5 min + session ensure |
| `lib/ha_session.py` | Keepalive + recovery orchestration |
| `lib/auto_login_core.py` | Xvfb headed Chromium + reCAPTCHA |
| `lib/session.py` | Cookies/CSRF validation (legacy, proven) |
| `lib/api_client.py` | Portal fetch + PDF |
| `lib/hidro_api.py` | Grid APIs, parsers |

### Shared (`lib/common/`)

- `chromium_lock.py` — global flock (Premier + Hidro never run browser together)
- `xvfb.py` — virtual display for headed browser on HA OS
- `health.py` — health.json helper

## Async model

All Selenium/requests run in `hass.async_add_executor_job()` — never block the event loop.

## Data flow

```
User credentials (Config Entry, encrypted)
        ↓
Coordinator._async_update_data()
        ↓
executor: ensure auth/session
        ↓
executor: API fetch
        ↓
Sensors updated via CoordinatorEntity
```

## Storage layout

```
/config/premier_energy/<entry_id>/
  token.txt
  browser_profile/
  invoices/
  health.json

/config/hidroelectrica/<entry_id>/
  secrets.json          # sync mirror for legacy lib (0600)
  session.json
  browser_profile/
  data.json
  invoices/
  health.json
```

HA Store (`.storage/`) holds metadata JSON per entry.

## Recovery

| Trigger | Premier | Hidro |
|---------|---------|-------|
| Scheduled poll | JWT refresh if exp < 20 min | keepalive ping |
| Invalid session | Selenium re-login | Xvfb auto-login |
| HA reboot | `async_config_entry_first_refresh` | same |
| Manual | `force_login` service / button | same |
