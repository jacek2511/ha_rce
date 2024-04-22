"""The sensor integration."""

from homeassistant.core import HomeAssistant

DOMAIN = "rce"

async def async_setup(hass: HomeAssistant, config):
    """Wstepna konfiguracja domeny, jeśli to konieczne."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
     """Set up PSE RCE from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "rce")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry):
    """Usunięcie integracji - skasowanie wpis konfiguracyjnego ."""
    return True
