"""Register support services for Hidroelectrica."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_EXPORT_SUPPORT_BUNDLE,
    SERVICE_OPEN_SUPPORT_LINK,
    SERVICE_REPORT_ISSUE,
)
from .lib.support import SUPPORT_LINKS


def register_support_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_OPEN_SUPPORT_LINK):
        return

    schema_link = vol.Schema(
        {
            vol.Optional("entry_id"): cv.string,
            vol.Optional("link"): vol.In(list(SUPPORT_LINKS.keys())),
        }
    )

    async def open_support_link(call: ServiceCall) -> None:
        link = call.data.get("link", "support")
        for coord in _coords(hass, call.data.get("entry_id")):
            await coord.async_notify_support_link(link)

    async def export_support_bundle(call: ServiceCall) -> None:
        for coord in _coords(hass, call.data.get("entry_id")):
            path = await coord.async_export_support_bundle()
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Hidroelectrica — Support Bundle",
                    "message": f"Export: `{path}`",
                    "notification_id": f"{DOMAIN}_bundle",
                },
            )

    async def report_issue(call: ServiceCall) -> None:
        template = call.data.get("template", "bug_report")
        for coord in _coords(hass, call.data.get("entry_id")):
            await coord.async_notify_support_link(template)

    hass.services.async_register(
        DOMAIN, SERVICE_OPEN_SUPPORT_LINK, open_support_link, schema=schema_link
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_SUPPORT_BUNDLE,
        export_support_bundle,
        schema=vol.Schema({vol.Optional("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPORT_ISSUE,
        report_issue,
        schema=vol.Schema(
            {
                vol.Optional("entry_id"): cv.string,
                vol.Optional("template"): vol.In(
                    ["bug_report", "auth_issue", "feature_request", "provider_change"]
                ),
            }
        ),
    )


def _coords(hass: HomeAssistant, entry_id: str | None):
    data = hass.data.get(DOMAIN, {})
    if entry_id:
        yield data[entry_id]
    else:
        yield from data.values()
