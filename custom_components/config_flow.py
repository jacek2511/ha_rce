"""PSE config flow"""

from homeassistant import config_entries
from . import DOMAIN


class PSECallendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id("pse_calendr_config_flow")
        self._abort_if_unique_id_configured()
        return self.async_show_form(step_id="hello")

    async def async_step_hello(self, user_input=None):
        """3. Krok logowania"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="hello")
