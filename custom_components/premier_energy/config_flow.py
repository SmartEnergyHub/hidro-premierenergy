"""Config flow for Premier Energy."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers import selector

from .const import CONF_EMAIL, DOMAIN
from .lib.auth_manager import PremierAuthManager

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class PremierEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow — email + password only."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()

            try:
                storage_dir = self.hass.config.path(DOMAIN, "validate")
                auth = PremierAuthManager(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                    storage_dir=storage_dir,
                    browser_profile=storage_dir / "browser_profile",
                    debug_dir=storage_dir / "debug",
                )
                await self.hass.async_add_executor_job(auth.refresh_token)
            except Exception as err:
                _LOGGER.error("Premier login validation failed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=f"Premier Energy ({user_input[CONF_EMAIL]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> config_entries.FlowResult:
        return await self.async_step_user()

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PremierOptionsFlowHandler(config_entry)


class PremierOptionsFlowHandler(config_entries.OptionsFlow):
    """Options — scan interval override (future)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return self.async_create_entry(title="", data=self.config_entry.options)
