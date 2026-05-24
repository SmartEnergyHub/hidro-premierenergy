"""Diagnostics for Hidroelectrica."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_TELEGRAM_BOT_TOKEN, DOMAIN
from .coordinator import HidroCoordinator

TO_REDACT = {CONF_PASSWORD, CONF_TELEGRAM_BOT_TOKEN, "csrf", "cookies"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: HidroCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.export_debug()
    data["username"] = entry.data.get("username")
    return async_redact_data(data, TO_REDACT)
