"""The RCE (PSE) integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform

from .const import (
    DOMAIN, 
    _LOGGER, 
    CONF_OPERATION_MODE, 
    CONF_PRICE_MODE
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration via YAML (not supported, but registers services)."""
    
    async def set_mode(call):
        mode = call.data.get("mode")
        price_mode = call.data.get("price_mode")
        
        for entry in hass.config_entries.async_entries(DOMAIN):
            new_options = dict(entry.options)
            
            # Aktualizujemy pod-tryb (comfort, eco itp.) jeśli podano
            if mode:
                new_options[CONF_OPERATION_MODE] = mode
            
            # Aktualizujemy główny tryb (low_price_cutoff, always_on itp.) jeśli podano
            if price_mode:
                new_options[CONF_PRICE_MODE] = price_mode

            hass.config_entries.async_update_entry(
                entry,
                options=new_options,
            )

    hass.services.async_register(DOMAIN, "set_operation_mode", set_mode)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RCE from a config entry."""
    _LOGGER.info("Setting up RCE config entry: %s", entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading RCE config entry: %s", entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
