"""Premier Energy integration setup."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, CoreState, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_DOWNLOAD_INVOICE,
    SERVICE_EXPORT_DEBUG,
    SERVICE_FORCE_LOGIN,
    SERVICE_REFRESH_SESSION,
    SERVICE_SEND_INDEX,
)
from .coordinator import PremierCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = PremierCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    @callback
    def _on_ha_start(event) -> None:
        """Refresh token la pornirea HA (evită token expirat după restart)."""
        async def _delayed_refresh(_now):
            if hass.state == CoreState.running:
                await coordinator.async_refresh_session()

        async_call_later(hass, 90, _delayed_refresh)

    entry.async_on_unload(
        hass.bus.async_listen_once("homeassistant_started", _on_ha_start)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH_SESSION):
        return

    async def refresh_session(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            await coord.async_refresh_session()

    async def force_login(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            await coord.async_force_login()

    async def download_invoice(call: ServiceCall) -> None:
        inv = call.data["invoice_number"]
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            path = await coord.async_download_invoice(inv)
            _LOGGER.info("Invoice PDF: %s", path)

    async def export_debug(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            _LOGGER.info("Premier debug: %s", coord.export_debug())

    async def send_index(call: ServiceCall) -> None:
        _LOGGER.warning("send_index: use entity button or extend with index value in service call")

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_SESSION,
        refresh_session,
        schema=vol.Schema({vol.Optional("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_LOGIN,
        force_login,
        schema=vol.Schema({vol.Optional("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DOWNLOAD_INVOICE,
        download_invoice,
        schema=vol.Schema(
            {
                vol.Required("invoice_number"): cv.string,
                vol.Optional("entry_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DEBUG,
        export_debug,
        schema=vol.Schema({vol.Optional("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_INDEX,
        send_index,
        schema=vol.Schema(
            {
                vol.Optional("entry_id"): cv.string,
                vol.Optional("index"): vol.Coerce(int),
            }
        ),
    )


def _coords(hass: HomeAssistant, entry_id: str | None):
    data = hass.data.get(DOMAIN, {})
    if entry_id:
        yield data[entry_id]
    else:
        yield from data.values()
