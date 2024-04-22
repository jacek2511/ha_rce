"""The sensor integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import asyncio

DOMAIN = "rce"

async def async_setup(hass: HomeAssistant, config: dict):
     """Set up the component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Set up PSE RCE from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "rce")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, "rce")
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
