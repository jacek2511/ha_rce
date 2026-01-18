"""Binary sensors for RCE (PSE)."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN, RESOLUTION_15M
from .entity import RCEBaseEntity


@dataclass(frozen=True)
class RCEBinarySensorDescription(BinarySensorEntityDescription):
    """RCE binary sensor description."""


BINARY_SENSORS: tuple[RCEBinarySensorDescription, ...] = (
    RCEBinarySensorDescription(
        key="low_price",
        translation_key="low_price",
    ),
    RCEBinarySensorDescription(
        key="tomorrow_data_available",
        translation_key="tomorrow_data_available",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for description in BINARY_SENSORS:
        if description.key == "low_price":
            entities.append(
                RCECheapNowBinarySensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    description=description,
                )
            )
        elif description.key == "tomorrow_data_available":
            entities.append(
                RCETwitterDataAvailableTomorrowBinarySensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    description=description,
                )
            )

    async_add_entities(entities)


class RCEBinarySensorBase(RCEBaseEntity, BinarySensorEntity):
    """Base class for RCE binary sensors."""

    def __init__(self, coordinator, entry_id: str, description: BinarySensorEntityDescription):
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self.entity_id = f"binary_sensor.rce_{description.key}"
        self._attr_unique_id = f"{entry_id}_{description.key}"


class RCECheapNowBinarySensor(RCEBinarySensorBase):
    """Binary sensor: cheap price now."""

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
            
        mask = data.get("cheap_mask_today")
        if not mask:
            return None

        res = data.get("resolution", RESOLUTION_15M)
        factor = 4 if res == RESOLUTION_15M else 1

        now = dt_util.now()
        idx = now.hour * factor + (now.minute // (60 // factor))

        if 0 <= idx < len(mask):
            return bool(mask[idx])

        return False

    @property
    def extra_state_attributes(self):
        """Dodajmy informację o statusie API do atrybutów."""
        return {"info": self.coordinator.data.get("api_status", "unknown")}


class RCETwitterDataAvailableTomorrowBinarySensor(RCEBinarySensorBase):
    """Binary sensor: tomorrow data available."""

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("prices_tomorrow"))

    @property
    def available(self) -> bool:
        return True
