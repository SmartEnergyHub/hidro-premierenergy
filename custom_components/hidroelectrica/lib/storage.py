"""Storage for Hidroelectrica integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..const import DOMAIN, STORAGE_KEY_SESSION, STORAGE_VERSION


class HidroStorage:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_SESSION}.{entry_id}")
        self.base_dir = Path(hass.config.config_dir) / DOMAIN / entry_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def async_load(self) -> dict[str, Any]:
        return await self._store.async_load() or {}

    async def async_save(self, data: dict[str, Any]) -> None:
        await self._store.async_save(data)

    def write_health_sync(self, payload: dict[str, Any]) -> None:
        (self.base_dir / "health.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
