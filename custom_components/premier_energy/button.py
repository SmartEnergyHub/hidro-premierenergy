"""Premier Energy buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, URL_DONATE
from .coordinator import PremierCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: PremierCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PremierRefreshButton(coordinator, entry),
            PremierForceLoginButton(coordinator, entry),
            PremierSupportDevelopmentButton(coordinator, entry),
            PremierExportSupportBundleButton(coordinator, entry),
            PremierOpenGitHubButton(coordinator, entry),
            PremierReportIssueButton(coordinator, entry),
        ]
    )


def _device_info(entry: ConfigEntry) -> dict:
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title,
        "manufacturer": "Premier Energy",
        "model": "Portal Client (gaze naturale)",
        "configuration_url": URL_DONATE,
    }


class PremierRefreshButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh_session"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = _device_info(entry)

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
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self.coordinator.async_force_login()


class PremierSupportDevelopmentButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "support_development"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:heart-outline"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_support_dev"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self.coordinator.async_notify_support_link("donate")


class PremierExportSupportBundleButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "export_support_bundle"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:package-down"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_export_bundle"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        path = await self.coordinator.async_export_support_bundle()
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Premier Energy — Support Bundle",
                "message": f"Pachet debug salvat (fără secrete): `{path}`",
                "notification_id": f"{DOMAIN}_bundle_export",
            },
        )


class PremierOpenGitHubButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "open_github"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:github"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_open_github"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self.coordinator.async_notify_support_link("github")


class PremierReportIssueButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "report_issue"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bug-outline"

    def __init__(self, coordinator: PremierCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_report_issue"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self.coordinator.async_notify_support_link("auth_issue")
