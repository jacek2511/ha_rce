"""The RCE (PSE) integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import *
from .coordinator import RCEDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup(hass: HomeAssistant, config) -> bool:
    
    async def set_mode(call):
        for entry in hass.config_entries.async_entries(DOMAIN):
            new_options = dict(entry.options)

            if "mode" in call.data:
                new_options[CONF_OPERATION_MODE] = call.data["mode"]
            if "price_mode" in call.data:
                new_options[CONF_PRICE_MODE] = call.data["price_mode"]

            hass.config_entries.async_update_entry(entry, options=new_options)

    hass.services.async_register(
        DOMAIN,
        "set_operation_mode",
        set_mode,
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    if not entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={
                CONF_TIME_RESOLUTION: DEFAULT_TIME_RESOLUTION,
                CONF_PRICE_MODE: DEFAULT_PRICE_MODE,
                CONF_OPERATION_MODE: DEFAULT_OPERATION_MODE,
                CONF_NEGATIVE_PRICES: DEFAULT_NEGATIVE_PRICES,
                CONF_CUSTOM_PEAK_HOURS_RANGE: DEFAULT_CUSTOM_PEAK_HOURS_RANGE,
                "comfort_percentile": 30,
                "comfort_min_window": 2,
                "consecutive_ranges_count": 4,
                "cheapest_not_consecutive_count": 4,
            }
        )

    coordinator = RCEDataUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(_reload))
    
    return True

async def _reload(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
    
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
