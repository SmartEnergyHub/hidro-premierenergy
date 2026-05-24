"""Premier Energy buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import PremierCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: PremierCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PremierRefreshButton(coordinator, entry),
            PremierForceLoginButton(coordinator, entry),
        ]
    )


class PremierRefreshButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh_session"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Premier Energy",
        }

    async def async_press(self) -> None:
        await self.coordinator.async_refresh_session()


class PremierForceLoginButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "force_login"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:login"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_force_login"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Premier Energy",
        }

    async def async_press(self) -> None:
        await self.coordinator.async_force_login()
