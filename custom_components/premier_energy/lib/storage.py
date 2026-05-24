"""Persistent storage adapter for Premier Energy (HA Store + local browser profile)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from ..const import DOMAIN, STORAGE_KEY_SESSION, STORAGE_VERSION


class PremierStorage:
    """Session/token storage backed by Home Assistant Store."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_SESSION}.{entry_id}",
        )
        self.base_dir = Path(hass.config.config_dir) / DOMAIN / entry_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.browser_profile = self.base_dir / "browser_profile"
        self.invoices_dir = self.base_dir / "invoices"
        self.debug_dir = self.base_dir / "debug"
        self.browser_profile.mkdir(parents=True, exist_ok=True)
        self.invoices_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    async def async_load(self) -> dict[str, Any]:
        data = await self._store.async_load()
        return data or {}

    async def async_save(self, data: dict[str, Any]) -> None:
        await self._store.async_save(data)

    @callback
    def token_path(self) -> Path:
        return self.base_dir / "token.txt"

    def read_token_sync(self) -> str | None:
        path = self.token_path()
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text or None

    def write_token_sync(self, token: str) -> None:
        self.token_path().write_text(token, encoding="utf-8")

    def write_health_sync(self, payload: dict[str, Any]) -> None:
        (self.base_dir / "health.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
