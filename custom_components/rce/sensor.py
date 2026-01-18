"""Platform for RCE (PSE) sensor integration – API v2 with Coordinator."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.util import dt as dt_util
from homeassistant.const import EntityCategory

from .const import (
    DOMAIN,
    DEFAULT_CURRENCY,
    DEFAULT_PRICE_TYPE,
    RESOLUTION_15M,
)
from .entity import RCEBaseEntity

# ------------------------------------------------------------
# DESCRIPTIONS
# ------------------------------------------------------------

@dataclass(frozen=True)
class RCESensorDescription(SensorEntityDescription):
    """RCE sensor description."""


SENSORS: tuple[RCESensorDescription, ...] = (
    RCESensorDescription(
        key="electricity_market_price",
        translation_key="electricity_market_price",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}",
    ),
    RCESensorDescription(
        key="cheapest_price_today",
        translation_key="cheapest_price_today",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}",
    ),
    RCESensorDescription(
        key="cheapest_hour_tomorrow",
        translation_key="cheapest_hour_tomorrow",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    RCESensorDescription(
        key="next_cheap_window",
        translation_key="next_cheap_window",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    RCESensorDescription(
        key="api_status",
        translation_key="api_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RCESensorDescription(
        key="last_successful_update",
        translation_key="last_successful_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)



# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for description in SENSORS:
        if description.key == "electricity_market_price":
            entities.append(
                RCEMarketPriceSensor(coordinator, entry.entry_id, description)
            )
        elif description.key == "cheapest_price_today":
            entities.append(
                RCECheapestPriceTodaySensor(coordinator, entry.entry_id, description)
            )
        elif description.key == "cheapest_hour_tomorrow":
            entities.append(
                RCECheapestHourTomorrowSensor(coordinator, entry.entry_id, description)
            )
        elif description.key == "next_cheap_window":
            entities.append(
                RCENextCheapWindowSensor(coordinator, entry.entry_id, description)
            )
        elif description.key == "api_status":
            entities.append(
                RCEApiStatusSensor(coordinator, entry.entry_id, description)
            )
        elif description.key == "last_successful_update":
            entities.append(
                RCELastSuccessfulUpdateSensor(coordinator, entry.entry_id, description)
            )

    async_add_entities(entities)


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def get_current_index(data) -> int:
    now = dt_util.now()
    res = data.get("resolution", RESOLUTION_15M)
    factor = 4 if res == RESOLUTION_15M else 1
    return now.hour * factor + (now.minute // (60 // factor))


# ------------------------------------------------------------
# BASE SENSOR
# ------------------------------------------------------------

class RCESensorBase(RCEBaseEntity, SensorEntity):
    """Base class for RCE sensors."""

    def __init__(self, coordinator, entry_id: str, description: SensorEntityDescription):
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self.entity_id = f"sensor.rce_{description.key}"
        self._attr_unique_id = f"{entry_id}_{description.key}"


# ------------------------------------------------------------
# SENSORS
# ------------------------------------------------------------

class RCEMarketPriceSensor(RCESensorBase):
    """Current electricity market price."""

    @property
    def native_value(self):
        prices = self.coordinator.data.get("prices_today")
        if not prices:
            return None

        idx = get_current_index(self.coordinator.data)
        if 0 <= idx < len(prices):
            return prices[idx]

        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        stats = data.get("stats", {})

        return {
            "price_mode": data.get("price_mode"),
            "operation_mode": data.get("operation_mode"),
            "peak_range": data.get("peak_range"),
            "average": stats.get("average"),
            "min": stats.get("min"),
            "max": stats.get("max"),
            "median": stats.get("median"),
            "prices_today": data.get("prices_today"),
            "cheap_mask_today": data.get("cheap_mask_today"),
            "prices_tomorrow": data.get("prices_tomorrow"),
            "cheap_mask_tomorrow": data.get("cheap_mask_tomorrow"),
        }


class RCECheapestPriceTodaySensor(RCESensorBase):
    """Cheapest price today."""

    @property
    def native_value(self):
        return self.coordinator.data.get("stats", {}).get("min")


class RCECheapestHourTomorrowSensor(RCESensorBase):
    """Cheapest hour tomorrow."""

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data or data.get("api_status") != "ok":
            return None
            
        prices = data.get("prices_tomorrow")
        if not prices:
            return None

        res = data.get("resolution", RESOLUTION_15M)
        factor = 4 if res == RESOLUTION_15M else 1

        idx = prices.index(min(prices))
        hour = idx // factor
        minute = (idx % factor) * (60 // factor)

        # Kluczowe dla uniknięcia "13 godzin temu"
        tomorrow = dt_util.now() + timedelta(days=1)
        
        return tomorrow.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        
        if data.get("api_status") != "ok":
            return {"info": "API error"}

        if not data.get("prices_tomorrow"):
            return {"info": "Waiting for tomorrow data"}
        
        return {"info": "API ok"}

    @property
    def icon(self) -> str:
        data = self.coordinator.data or {}
        if data.get("api_status") != "ok":
            return "mdi:alert-circle-outline"
        if not data.get("prices_tomorrow"):
            return "mdi:clock-wait"
        return "mdi:cash-clock"


class RCENextCheapWindowSensor(RCESensorBase):
    """Next cheap window today."""

    @property                                                                                      
    def available(self) -> bool:                                                                   
        return True                                                                                

    @property
    def native_value(self):
        data = self.coordinator.data
        mask = data.get("cheap_mask_today")

        if not mask:
            return None

        res = data.get("resolution", RESOLUTION_15M)
        factor = 4 if res == RESOLUTION_15M else 1

        now = dt_util.now()
        idx = get_current_index(data)

        if 0 <= idx < len(mask) and mask[idx]:
            hour = idx // factor
            minute = (idx % factor) * (60 // factor)
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        for i in range(idx + 1, len(mask)):
            if mask[i]:
                hour = i // factor
                minute = (i % factor) * (60 // factor)
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return None

    @property
    def extra_state_attributes(self):
        has_window = self.native_value is not None
        
        return {
            "info": "No cheap windows available today" if not has_window else "Cheap window found",
            "cheap_window_available": has_window
        }


class RCEApiStatusSensor(RCESensorBase):
    """Diagnostic sensor: API status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("api_status", "unknown")

    @property
    def available(self) -> bool:
        return True

class RCELastSuccessfulUpdateSensor(RCESensorBase):
    """Diagnostic sensor: last successful API update."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.coordinator.last_successful_update

    @property
    def available(self) -> bool:
        return True
        
