"""The RCE component."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, _LOGGER

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this integration using YAML is not supported."""
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info("RCE-async_setup")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RCE integration."""
    _LOGGER.info("RCE-async_setup_entry " + str(entry))
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("RCE-async_unload_entry remove entities")
    await hass.config_entries.async_forward_entry_unload(entry, Platform.SENSOR)
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
     """Reload config entry."""
     await async_unload_entry(hass, entry)
     await async_setup_entry(hass, entry)
