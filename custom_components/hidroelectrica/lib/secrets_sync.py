"""Write secrets.json for legacy lib code from HA config entry."""

from __future__ import annotations

import json
from pathlib import Path


def write_secrets_sync(
    base_dir: Path,
    username: str,
    password: str,
    telegram_bot_token: str = "",
    telegram_chat_id: str = "",
    **extra: str,
) -> None:
    payload = {
        "username": username,
        "password": password,
        "telegram_bot_token": telegram_bot_token,
        "telegram_chat_id": telegram_chat_id,
        **extra,
    }
    path = base_dir / "secrets.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    path.chmod(0o600)
