"""Hidroelectrica sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HidroCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: HidroCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HidroInvoiceAmountSensor(coordinator, entry),
            HidroInvoiceNumberSensor(coordinator, entry),
            HidroDueDateSensor(coordinator, entry),
            HidroPodSensor(coordinator, entry),
            HidroBalanceSensor(coordinator, entry),
            HidroIndexSensor(coordinator, entry),
            HidroConsumptionSensor(coordinator, entry),
        ]
    )


class HidroBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HidroCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Hidroelectrica",
            "model": "iHidro Portal",
        }


class HidroInvoiceAmountSensor(HidroBase):
    _attr_translation_key = "invoice_amount"
    _attr_native_unit_of_measurement = "RON"
    _attr_icon = "mdi:cash"

    @property
    def native_value(self):
        u = (self.coordinator.data or {}).get("ultima_factura") or {}
        return u.get("suma")


class HidroInvoiceNumberSensor(HidroBase):
    _attr_translation_key = "invoice_number"
    _attr_icon = "mdi:file-document-outline"

    @property
    def native_value(self):
        u = (self.coordinator.data or {}).get("ultima_factura") or {}
        return u.get("numar")


class HidroDueDateSensor(HidroBase):
    _attr_translation_key = "due_date"
    _attr_icon = "mdi:calendar"

    @property
    def native_value(self):
        u = (self.coordinator.data or {}).get("ultima_factura") or {}
        sc = u.get("scadenta") or ""
        if len(sc) >= 10 and sc[4] == "-":
            p = sc[:10].split("-")
            return f"{p[2]}/{p[1]}/{p[0]}"
        return sc or None


class HidroPodSensor(HidroBase):
    _attr_translation_key = "pod"
    _attr_icon = "mdi:transmission-tower"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("pod")


class HidroBalanceSensor(HidroBase):
    _attr_translation_key = "balance"
    _attr_native_unit_of_measurement = "RON"
    _attr_icon = "mdi:wallet"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("sold")


class HidroIndexSensor(HidroBase):
    _attr_translation_key = "index_current"
    _attr_native_unit_of_measurement = "kWh"
    _attr_icon = "mdi:counter"

    @property
    def native_value(self):
        idx = (self.coordinator.data or {}).get("index") or {}
        return idx.get("curent")


class HidroConsumptionSensor(HidroBase):
    _attr_translation_key = "consumption_avg"
    _attr_native_unit_of_measurement = "RON"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:flash"

    @property
    def native_value(self):
        c = (self.coordinator.data or {}).get("consum") or {}
        return c.get("media_lunara_lei")
