"""Hidroelectrica binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HidroCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: HidroCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HidroSessionSensor(coordinator, entry),
            HidroAutocitireSensor(coordinator, entry),
        ]
    )


class HidroSessionSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "session_ok"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: HidroCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_session"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Hidroelectrica",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.session_ok)


class HidroAutocitireSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "self_reading_period"
    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: HidroCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_autocitire"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Hidroelectrica",
        }

    @property
    def is_on(self) -> bool:
        idx = (self.coordinator.data or {}).get("index") or {}
        return bool(idx.get("autocitire_activa"))
