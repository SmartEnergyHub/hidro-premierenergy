"""Hidroelectrica integration setup."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, HomeAssistant, ServiceCall, callback
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
    SERVICE_SEND_LAST_INVOICE_TELEGRAM,
)
from .coordinator import HidroCoordinator
from .support_services import register_support_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = HidroCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    @callback
    def _on_ha_start(_event) -> None:
        """Recovery sesiune după restart HA (cookies/token CSRF)."""

        async def _delayed_refresh(_now) -> None:
            if hass.state != CoreState.running:
                return
            _LOGGER.info("Hidroelectrica: session recovery la pornirea HA")
            await coordinator.async_refresh_session()

        async_call_later(hass, 90, _delayed_refresh)

    entry.async_on_unload(hass.bus.async_listen_once("homeassistant_started", _on_ha_start))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    register_support_services(hass)
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
        for coord in _coords(hass, call.data.get("entry_id")):
            await coord.async_refresh_session()

    async def force_login(call: ServiceCall) -> None:
        for coord in _coords(hass, call.data.get("entry_id")):
            await coord.async_force_login()

    async def download_invoice(call: ServiceCall) -> None:
        inv = call.data["invoice_number"]
        for coord in _coords(hass, call.data.get("entry_id")):
            path = await coord.async_download_invoice(inv)
            _LOGGER.info("Hidro PDF: %s", path)

    async def send_index(call: ServiceCall) -> None:
        from .lib.index_resolve import resolve_index_from_call

        index_val = resolve_index_from_call(hass, call)
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            result = await coord.async_send_index(index_val)
            _LOGGER.info("Hidro send_index OK: %s — %s", index_val, result[:120])

    async def send_last_invoice_telegram(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        for coord in _coords(hass, entry_id):
            numar = await coord.async_send_last_invoice_telegram()
            _LOGGER.info("Hidro factură Telegram: %s", numar)

    async def export_debug(call: ServiceCall) -> None:
        for coord in _coords(hass, call.data.get("entry_id")):
            _LOGGER.info("Hidro debug: %s", coord.export_debug())

    schema_entry = vol.Schema({vol.Optional("entry_id"): cv.string})
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_SESSION, refresh_session, schema=schema_entry
    )
    hass.services.async_register(DOMAIN, SERVICE_FORCE_LOGIN, force_login, schema=schema_entry)
    hass.services.async_register(
        DOMAIN,
        SERVICE_DOWNLOAD_INVOICE,
        download_invoice,
        schema=schema_entry.extend({vol.Required("invoice_number"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_INDEX,
        send_index,
        schema=schema_entry.extend({vol.Optional("index"): vol.Coerce(int)}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_LAST_INVOICE_TELEGRAM,
        send_last_invoice_telegram,
        schema=schema_entry,
    )
    hass.services.async_register(DOMAIN, SERVICE_EXPORT_DEBUG, export_debug, schema=schema_entry)


def _coords(hass: HomeAssistant, entry_id: str | None):
    data = hass.data.get(DOMAIN, {})
    if entry_id:
        yield data[entry_id]
    else:
        yield from data.values()
