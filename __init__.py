"""The RCE component."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict):
     """Set up the component."""
     hass.data[DOMAIN] = {}
     return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Set up PSE RCE integration."""
     hass.async_create_task(
          hass.config_entries.async_forward_entry_setup(entry, "rce")
     )
     return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Unload a config entry."""
     if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
          hass.data[DOMAIN].pop(entry.entry_id)

     return unload_ok
