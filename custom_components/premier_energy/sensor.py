"""Premier Energy sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PremierCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: PremierCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PremierInvoiceAmountSensor(coordinator, entry),
            PremierInvoiceNumberSensor(coordinator, entry),
            PremierDueDateSensor(coordinator, entry),
            PremierConsumptionM3Sensor(coordinator, entry),
            PremierConsumptionMWhSensor(coordinator, entry),
            PremierAddressSensor(coordinator, entry),
            PremierTokenMarginSensor(coordinator, entry),
        ]
    )


class PremierBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Premier Energy",
            "model": "Portal Client",
        }


class PremierInvoiceAmountSensor(PremierBaseSensor):
    _attr_translation_key = "invoice_amount"
    _attr_native_unit_of_measurement = "RON"
    _attr_icon = "mdi:cash"

    @property
    def native_value(self):
        return self.coordinator.data.get("ultima_factura_suma") if self.coordinator.data else None


class PremierInvoiceNumberSensor(PremierBaseSensor):
    _attr_translation_key = "invoice_number"
    _attr_icon = "mdi:file-document-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get("numar_factura") if self.coordinator.data else None


class PremierDueDateSensor(PremierBaseSensor):
    _attr_translation_key = "due_date"
    _attr_icon = "mdi:calendar"

    @property
    def native_value(self):
        return self.coordinator.data.get("scadenta") if self.coordinator.data else None


class PremierConsumptionM3Sensor(PremierBaseSensor):
    _attr_translation_key = "consumption_m3"
    _attr_native_unit_of_measurement = "m³"
    _attr_icon = "mdi:meter-gas"

    @property
    def native_value(self):
        return self.coordinator.data.get("consum_m3") if self.coordinator.data else None


class PremierConsumptionMWhSensor(PremierBaseSensor):
    _attr_translation_key = "consumption_mwh"
    _attr_native_unit_of_measurement = UnitOfEnergy.MEGA_WATT_HOUR
    _attr_icon = "mdi:fire"

    @property
    def native_value(self):
        return self.coordinator.data.get("consum_mwh") if self.coordinator.data else None


class PremierAddressSensor(PremierBaseSensor):
    _attr_translation_key = "address"
    _attr_icon = "mdi:home-map-marker"

    @property
    def native_value(self):
        return self.coordinator.data.get("adresa") if self.coordinator.data else None


class PremierTokenMarginSensor(PremierBaseSensor):
    _attr_translation_key = "token_margin"
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:timer-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get("token_margin_sec") if self.coordinator.data else None
