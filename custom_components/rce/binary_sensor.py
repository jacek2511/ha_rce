"""Binary sensors for RCE (PSE)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, RESOLUTION_15M

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RCE binary sensors."""
    # W nowym modelu coordinator jest tworzony w sensor.py. 
    # Aby uniknąć błędów inicjalizacji, importujemy klasę koordynatora.
    from .sensor import RCEDataUpdateCoordinator
    
    coordinator = RCEDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([RCECheapNowBinarySensor(coordinator, entry.entry_id)])


class RCECheapNowBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor representing if the energy is currently cheap."""
    
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_has_entity_name = True
    _attr_translation_key = "low_price"  # To powiąże sensor z plikiem JSON

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_low_price"
        self.entity_id = "binary_sensor.rce_low_price"

    @property
    def is_on(self) -> bool | None:
        """Return true if current hour/slot is marked as cheap in the mask."""
        mask = self.coordinator.data.get("cheap_mask_today", [])
        if not mask:
            return None

        # Pobieramy rozdzielczość i obliczamy aktualny indeks w masce
        res = self.coordinator.data.get("resolution", RESOLUTION_15M)
        factor = 4 if res == RESOLUTION_15M else 1
        
        import homeassistant.util.dt as dt_util
        now = dt_util.now()
        idx = now.hour * factor + (now.minute // (60 // factor))

        if 0 <= idx < len(mask):
            return mask[idx]
        
        return False
