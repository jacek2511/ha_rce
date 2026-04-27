"""RCE sensors"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DEFAULT_CURRENCY,
    DEFAULT_PRICE_TYPE,
    RESOLUTION_15M,
)
from .entity import RCEBaseEntity


# ============================================================
# DESCRIPTIONS
# ============================================================
@dataclass(frozen=True)
class RCESensorDescription(SensorEntityDescription):
    pass


SENSORS: tuple[RCESensorDescription, ...] = (
    # --- PRICES ---
    RCESensorDescription(
        key="electricity_market_price",
        translation_key="electricity_market_price",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}",
    ),
    RCESensorDescription(
        key="next_price",
        translation_key="next_price",
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
    ),
    RCESensorDescription(
        key="next_cheap_window_tomorrow",
        translation_key="next_cheap_window_tomorrow",
    ),
    RCESensorDescription(
        key="best_window_today",
        translation_key="best_window_today",
    ),
    RCESensorDescription(
        key="best_window_tomorrow",
        translation_key="best_window_tomorrow",
    ),
    RCESensorDescription(
        key="top3_windows_today",
        translation_key="top3_windows_today",
    ),
    RCESensorDescription(
        key="top3_windows_tomorrow",
        translation_key="top3_windows_tomorrow",
    ),
    
    # --- DIAGNOSTICS ---
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

# ============================================================
# SETUP
# ============================================================
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for description in SENSORS:
        key = description.key

        if key == "electricity_market_price":
            entities.append(RCEMarketPriceSensor(coordinator, entry.entry_id, description))

        elif key == "next_price":
            entities.append(RCENextPriceSensor(coordinator, entry.entry_id, description))

        elif key == "cheapest_price_today":
            entities.append(RCECheapestPriceTodaySensor(coordinator, entry.entry_id, description))

        elif key == "cheapest_hour_tomorrow":
            entities.append(RCECheapestHourTomorrowSensor(coordinator, entry.entry_id, description))

        elif key == "next_cheap_window":
            entities.append(RCENextCheapWindowSensor(coordinator, entry.entry_id, description))

        elif key == "next_cheap_window_tomorrow":
            entities.append(RCENextCheapWindowTomorrowSensor(coordinator, entry.entry_id, description))

        elif key == "best_window_today":
            entities.append(RCEBestWindowTodaySensor(coordinator, entry.entry_id, description))

        elif key == "best_window_tomorrow":
            entities.append(RCEBestWindowTomorrowSensor(coordinator, entry.entry_id, description))

        elif key == "top3_windows_today":
            entities.append(RCETop3WindowsTodaySensor(coordinator, entry.entry_id, description))

        elif key == "top3_windows_tomorrow":
            entities.append(RCETop3WindowsTomorrowSensor(coordinator, entry.entry_id, description))

        elif key == "api_status":
            entities.append(RCEApiStatusSensor(coordinator, entry.entry_id, description))

        elif key == "last_successful_update":
            entities.append(RCELastSuccessfulUpdateSensor(coordinator, entry.entry_id, description))

    async_add_entities(entities)


# ============================================================
# HELPERS
# ============================================================
def get_current_index():
    now = dt_util.now()
    return now.hour * 4 + (now.minute // 15)

def idx_to_time(i, factor):
    h = i // factor
    m = (i % factor) * (60 // factor)
    return f"{h:02d}:{m:02d}"

def format_range(start, end, factor):
    return f"{idx_to_time(start, factor)} - {idx_to_time(end, factor)}"

def find_next_window(mask, start_idx):
    if not mask:
        return None, None

    start = None
    end = None
    for i in range(start_idx, len(mask)):
        if mask[i]:
            start = i
            break

    if start is None:
        return None, None

    for i in range(start, len(mask)):
        if not mask[i]:
            end = i
            break

    if end is None:
        end = len(mask)

    return start, end

# ============================================================
# BASE
# ============================================================
class RCESensorBase(RCEBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, description):
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self.entity_id = f"sensor.rce_{description.key}"

    @property
    def available(self):
        return self.coordinator.data is not None

class RCEWindowBaseSensor(RCESensorBase):
    day_key = "today"

    def _get_data(self):
        data = self.coordinator.data
        return (
            data.get(f"cheap_mask_{self.day_key}"),
            data.get(f"prices_{self.day_key}"),
            data,
        )

    def _factor(self, data):
        return 4 if data.get("resolution") == RESOLUTION_15M else 1

# ============================================================
# CORE SENSORS
# ============================================================
class RCEMarketPriceSensor(RCESensorBase):                                                             
    """Current electricity market price."""                                                            
                                                                                                       
    @property                                                                                          
    def native_value(self):                                                                            
        prices = self.coordinator.data.get("prices_today")                                             
        if not prices:                                                                                 
            return None                                                                                
                                                                                                       
        idx = get_current_index()                                                                      
        return prices[idx] if idx < len(prices) else None                                              
                                                                                                       
    @property                                                                                          
    def extra_state_attributes(self):                                                                  
        data = self.coordinator.data or {}                                                             
        stats = data.get("stats", {})                                                                  
                                                                                                       
        return {                                                                                       
            "price_mode": data.get("price_mode"),                                                      
            "operation_mode": data.get("operation_mode"),                                              
            "peak_range": data.get("peak_range"),                                                      
            "average": stats.get("average"),                                                           
            "min": stats.get("min"),                                                                   
            "max": stats.get("max"),                                                                   
            "median": stats.get("median"),                                                             
            "low_price_cutoff": data.get("low_price_cutoff"),                                          
            "prices_today": data.get("prices_today"),                                                  
            "cheap_mask_today": data.get("cheap_mask_today"),                                          
            "prices_tomorrow": data.get("prices_tomorrow"),                                            
            "cheap_mask_tomorrow": data.get("cheap_mask_tomorrow"),                                    
        }                                                                                              
                                                            

class RCENextPriceSensor(RCESensorBase):
    @property
    def native_value(self):
        data = self.coordinator.data
        prices = data.get("prices_today")

        if not prices:
            return None

        idx = get_current_index() + 1
        if idx < len(prices):
            return prices[idx]

        if data.get("prices_tomorrow"):
            return data["prices_tomorrow"][0]

        return None

# ============================================================
# WINDOW SENSORS
# ============================================================
class RCENextCheapWindowSensor(RCEWindowBaseSensor):                                                   
    day_key = "today"                                                                                  
                                                                                                       
    def _start_index(self):                                                                            
        return get_current_index() if self.day_key == "today" else 0                                   
                                                                                                       
    @property                                                                                          
    def native_value(self):                                                                            
        mask, _, data = self._get_data()                                                               
        if not mask:                                                                                   
            return None                                                                                
                                                                                                       
        start, end = find_next_window(mask, self._start_index())                                       
                                                                                                       
        if start is None:                                                                              
            return None                                                                                
                                                                                                       
        return format_range(start, end, self._factor(data)) 
        
class RCENextCheapWindowTomorrowSensor(RCENextCheapWindowSensor):
    day_key = "tomorrow"

# ============================================================
# BEST WINDOW
# ============================================================
class RCEBestWindowBase(RCEWindowBaseSensor):
    def _get_best(self):
        data = self.coordinator.data
        key = f"best_window_{self.day_key}" if self.day_key == "tomorrow" else "best_window"
        return data.get(key)

    @property
    def native_value(self):
        best = self._get_best()
        if not best:
            return None

        data = self.coordinator.data
        return format_range(best["start"], best["end"], self._factor(data))

    @property
    def extra_state_attributes(self):
        best = self._get_best()
        if not best:
            return {}

        data = self.coordinator.data
        avg_day = data.get("stats", {}).get("average")

        return {
            "avg_price": best["avg"],
            "min_price": best["min"],
            "max_price": best["max"],
            "duration_slots": best["end"] - best["start"],
            "savings_vs_avg_day": round(avg_day - best["avg"], 2)
            if avg_day else None,
        }

class RCEBestWindowTodaySensor(RCEBestWindowBase):
    day_key = "today"

class RCEBestWindowTomorrowSensor(RCEBestWindowBase):
    day_key = "tomorrow"

# ============================================================
# TOP 3
# ============================================================
class RCETop3WindowsBase(RCEWindowBaseSensor):
    def _get_top(self):
        data = self.coordinator.data
        key = f"top_windows_{self.day_key}" if self.day_key == "tomorrow" else "top_windows"
        return data.get(key)

    @property
    def native_value(self):
        top = self._get_top()
        return f"{len(top)} windows" if top else None

    @property
    def extra_state_attributes(self):
        top = self._get_top()
        if not top:
            return {}

        data = self.coordinator.data
        factor = self._factor(data)

        return {
            "windows": [
                {
                    "range": format_range(w["start"], w["end"], factor),
                    "avg_price": w["avg"],
                    "min_price": w["min"],
                    "max_price": w["max"],
                    "duration_slots": w["end"] - w["start"],
                }
                for w in top
            ]
        }

class RCETop3WindowsTodaySensor(RCETop3WindowsBase):
    day_key = "today"

class RCETop3WindowsTomorrowSensor(RCETop3WindowsBase):
    day_key = "tomorrow"

class RCECheapestPriceTodaySensor(RCESensorBase):
    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return data.get("stats", {}).get("min") if data.get("api_status") == "ok" else None

class RCECheapestHourTomorrowSensor(RCESensorBase):
    @property
    def native_value(self):
        data = self.coordinator.data or {}

        if data.get("api_status") != "ok":
            return None

        prices = data.get("prices_tomorrow")
        if not prices:
            return None

        idx = prices.index(min(prices))
        factor = 4 if data.get("resolution") == RESOLUTION_15M else 1
        hour = idx // factor
        minute = (idx % factor) * (60 // factor)
        tomorrow = dt_util.now() + timedelta(days=1)

        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

# ============================================================
# DIAGNOSTIC
# ============================================================
class RCEApiStatusSensor(RCESensorBase):
    @property
    def native_value(self):
        return self.coordinator.data.get("api_status")

class RCELastSuccessfulUpdateSensor(RCESensorBase):
    @property
    def native_value(self):
        return self.coordinator.last_successful_update

