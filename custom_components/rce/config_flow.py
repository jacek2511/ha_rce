"""RCE PSE config flow"""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)

from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_CUSTOM_PEAK_HOURS_RANGE,
    CONF_LOW_PRICE_CUTOFF,
    CONF_NUMBER_OF_CHEAPEST_HOURS,
    CONF_PRICE_MODE,
    DEFAULT_CUSTOM_PEAK_HOURS_RANGE,
    DEFAULT_LOW_PRICE_CUTOFF,
    DEFAULT_NUMBER_OF_CHEAPEST_HOURS,
    DEFAULT_PRICE_MODE,
    PRICE_MODES,
)

RE_HOURS_RANGE = re.compile(r"^/d{1,2}-/d{1,2}$")


class PSESensorConfigFlow(ConfigFlow, domain=DOMAIN):

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> PSESensorOptionFlow:
        """Get the options flow for this handler."""
        return PSESensorOptionFlow(config_entry)


    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id("pse_sensor_config_flow")
        self._abort_if_unique_id_configured()
        return self.async_show_form(step_id="hello")

    async def async_step_hello(self, user_input=None):
        """3. Krok logowania"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="hello")

class PSESensorOptionFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CUSTOM_PEAK_HOURS_RANGE,
                        default=self.config_entry.options.get(
                            CONF_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_CUSTOM_PEAK_HOURS_RANGE
                        ),
                    ): str,
                    vol.Optional(
                        CONF_LOW_PRICE_CUTOFF,
                        default=self.config_entry.options.get(
                            CONF_LOW_PRICE_CUTOFF, DEFAULT_LOW_PRICE_CUTOFF
                        ),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_NUMBER_OF_CHEAPEST_HOURS,
                        default=self.config_entry.options.get(
                            CONF_NUMBER_OF_CHEAPEST_HOURS, DEFAULT_NUMBER_OF_CHEAPEST_HOURS
                        ),
                    ): vol.Coerce(int),
                    vol.Optional(
                       CONF_PRICE_MODE,
                       default=self.config_entry.options.get(
                           CONF_PRICE_MODE, DEFAULT_PRICE_MODE
                        ),
                    ): vol.In(PRICE_MODES), 
                }
            ),
            errors=errors,
        )
