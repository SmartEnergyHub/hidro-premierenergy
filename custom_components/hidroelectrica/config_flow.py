"""Config flow for Hidroelectrica."""

from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers import selector

from .const import (
    CONF_TELEGRAM_BOT_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_USERNAME,
    DOMAIN,
)
from .lib.ha_session import ensure_session, setup_storage_dir
from .lib.secrets_sync import write_secrets_sync

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_TELEGRAM_BOT_TOKEN): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_TELEGRAM_CHAT_ID): selector.TextSelector(),
    }
)


class HidroelectricaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            try:
                base = self.hass.config.path(DOMAIN, "validate")
                setup_storage_dir(base)
                write_secrets_sync(
                    base,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    telegram_bot_token=user_input.get(CONF_TELEGRAM_BOT_TOKEN, ""),
                    telegram_chat_id=user_input.get(CONF_TELEGRAM_CHAT_ID, ""),
                )
                os.environ["HIDROELECTRICA_DIR"] = str(base)
                ok = await self.hass.async_add_executor_job(ensure_session)
                if not ok:
                    raise RuntimeError("Login failed")
            except Exception as err:
                _LOGGER.error("Hidro validation failed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=f"Hidroelectrica ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
