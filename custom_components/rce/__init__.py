"""The RCE component."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: configType) -> bool:
     """Set up the component."""
     hass.data[DOMAIN] = {}
     return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Set up RCE integration."""
     hass.async_create_task(
          hass.config_entries.async_forward_entry_setup(entry, DOMAIN)
     )
     return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Unload a config entry."""
     unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)
     
     if unload_ok:
          hass.data[DOMAIN].pop(entry.entry_id)
          return unload_ok
     return False
     

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
     """Reload config entry."""
     await async_unload_entry(hass, entry)
     await async_setup_entry(hass, entry)
