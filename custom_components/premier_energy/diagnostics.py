"""Diagnostics for Premier Energy."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import PremierCoordinator

TO_REDACT = {CONF_PASSWORD, "token", "id_token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: PremierCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.export_debug()
    data["email"] = entry.data.get(CONF_EMAIL)
    data["coordinator_data_keys"] = list((coordinator.data or {}).keys())
    return async_redact_data(data, TO_REDACT)
