from __future__ import annotations

import voluptuous as vol
import re
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    PRICE_MODES,
    CONF_CUSTOM_PEAK_HOURS_RANGE,
    CONF_PRICE_MODE,
    CONF_NEGATIVE_PRICES,
    CONF_TIME_RESOLUTION,
    DEFAULT_CUSTOM_PEAK_HOURS_RANGE,
    DEFAULT_PRICE_MODE,
    DEFAULT_NEGATIVE_PRICES,
    DEFAULT_TIME_RESOLUTION,
    RESOLUTION_15M,
    RESOLUTION_1H,
    CONF_OPERATION_MODE,
    OPERATION_MODES,
    DEFAULT_OPERATION_MODE,
    CONF_CONSECUTIVE_COUNT,
    CONF_NOT_CONSECUTIVE_COUNT,
)

def validate_hour_range(value: str) -> bool:
    pattern = r"^\d{1,2}-\d{1,2}$"
    if not re.match(pattern, value):
        return False
    
    try:
        start, end = map(int, value.split("-"))
        return 0 <= start < 24 and 0 <= end <= 24 and start < end
    except ValueError:
        return False


class RCEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="PSE Market Electricity Price (RCE)",
                data={},
            )

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RCEOptionsFlowHandler(config_entry)


class RCEOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()

    async def async_step_init(self, user_input=None):
        errors = {}
        options = self.config_entry.options

        if user_input is not None:
            if not validate_hour_range(user_input.get(CONF_CUSTOM_PEAK_HOURS_RANGE, "")):
                errors[CONF_CUSTOM_PEAK_HOURS_RANGE] = "invalid_hour_range"
            else:
                return self.async_create_entry(title="", data=user_input)

        current_settings = (
            f"Obecne ustawienia:\n"
            f"SUPER ECO: {options.get('super_eco_percentile', 10)}% / {options.get('super_eco_min_window', 3)}h\n"
            f"ECO: {options.get('eco_percentile', 20)}% / {options.get('eco_min_window', 4)}h\n"
            f"COMFORT: {options.get('comfort_percentile', 30)}% / {options.get('comfort_min_window', 2)}h\n"
            f"AGGRESSIVE: {options.get('aggressive_percentile', 45)}% / {options.get('aggressive_min_window', 1)}h"
        )

        schema = vol.Schema({
            vol.Required(CONF_TIME_RESOLUTION, default=options.get(CONF_TIME_RESOLUTION, DEFAULT_TIME_RESOLUTION)): vol.In([RESOLUTION_15M, RESOLUTION_1H]),
            vol.Required(CONF_PRICE_MODE, default=options.get(CONF_PRICE_MODE, DEFAULT_PRICE_MODE)): vol.In(PRICE_MODES),
            vol.Required(CONF_CONSECUTIVE_COUNT, default=options.get(CONF_CONSECUTIVE_COUNT, 4)): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
            vol.Required(CONF_NOT_CONSECUTIVE_COUNT, default=options.get(CONF_NOT_CONSECUTIVE_COUNT, 4)): vol.All(vol.Coerce(int), vol.Range(min=1, max=96)),
            vol.Required(CONF_OPERATION_MODE, default=options.get(CONF_OPERATION_MODE, DEFAULT_OPERATION_MODE)): vol.In(OPERATION_MODES),
            vol.Required("super_eco_percentile", default=options.get("super_eco_percentile", 10)): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required("super_eco_min_window", default=options.get("super_eco_min_window", 3)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            vol.Required("eco_percentile", default=options.get("eco_percentile", 20)): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required("eco_min_window", default=options.get("eco_min_window", 4)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            vol.Required("comfort_percentile", default=options.get("comfort_percentile", 30)): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required("comfort_min_window", default=options.get("comfort_min_window", 2)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            vol.Required("aggressive_percentile", default=options.get("aggressive_percentile", 45)): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required("aggressive_min_window", default=options.get("aggressive_min_window", 1)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            vol.Required(CONF_NEGATIVE_PRICES, default=options.get(CONF_NEGATIVE_PRICES, DEFAULT_NEGATIVE_PRICES)): bool,
            vol.Required(CONF_CUSTOM_PEAK_HOURS_RANGE, default=options.get(CONF_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_CUSTOM_PEAK_HOURS_RANGE)): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={"current_status": current_settings}
        )
