"""Options flow — support links & telemetry opt-in."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_TELEMETRY_OPT_IN, DOMAIN, URL_DONATE
from .lib.support import URL_DISCUSSIONS, URL_DOCS, URL_GITHUB, URL_ISSUES


class PremierOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TELEMETRY_OPT_IN,
                    default=self.config_entry.options.get(CONF_TELEMETRY_OPT_IN, False),
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "donate_url": URL_DONATE,
                "github_url": URL_GITHUB,
                "issues_url": URL_ISSUES,
                "discussions_url": URL_DISCUSSIONS,
                "docs_url": URL_DOCS,
            },
        )
