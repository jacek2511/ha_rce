"""Platform for RCE (PSE) sensor integration – API v2 with Coordinator."""
from __future__ import annotations

import logging
import json
import requests
from datetime import timedelta
from statistics import mean, median

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DEFAULT_CURRENCY,
    DEFAULT_PRICE_TYPE,
    CONF_TIME_RESOLUTION,
    DEFAULT_TIME_RESOLUTION,
    RESOLUTION_15M,
    CONF_OPERATION_MODE,
    DEFAULT_OPERATION_MODE,
    CONF_PRICE_MODE,
    DEFAULT_PRICE_MODE,
    CONF_CUSTOM_PEAK_HOURS_RANGE,
)

_LOGGER = logging.getLogger(__name__)

URL = (
    "https://v2.api.raporty.pse.pl/api/rce-pln"
    "?$filter=business_date eq '{day}'"
    "&$select=dtime,rce_pln"
    "&$orderby=dtime"
)

async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Setup entities based on config entry."""
    coordinator = RCEDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    entry_id = config_entry.entry_id

    async_add_entities([
        RCESensor(coordinator, entry_id),
        RCENextCheapWindowSensor(coordinator, entry_id),
        RCECheapestPriceTodaySensor(coordinator, entry_id),
        RCECheapestHourTomorrowSensor(coordinator, entry_id),
    ])

class RCEDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from PSE and calculate low price windows."""
    def __init__(self, hass, config_entry):
        self.config_entry = config_entry
        super().__init__(hass, _LOGGER, name="RCE Coordinator", update_interval=timedelta(minutes=15))

    async def _fetch_day_data(self, offset: int):
        target_date = dt_util.now() + timedelta(days=offset)
        date_str = target_date.strftime("%Y-%m-%d")
        try:
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(URL.format(day=date_str), timeout=20)
            )
            if response.status_code == 200:
                return json.loads(response.text).get("value", [])
        except Exception as err:
            _LOGGER.warning("Connection error for %s: %s", date_str, err)
        return []

    async def _async_update_data(self):
        options = self.config_entry.options
        res = options.get(CONF_TIME_RESOLUTION, DEFAULT_TIME_RESOLUTION)
        price_mode = options.get(CONF_PRICE_MODE, DEFAULT_PRICE_MODE)
        operation_mode = options.get(CONF_OPERATION_MODE, DEFAULT_OPERATION_MODE)                                     
        peak_range_str = options.get(CONF_CUSTOM_PEAK_HOURS_RANGE, "00-24")
        
        raw_today = await self._fetch_day_data(0)
        if not raw_today:
            raise UpdateFailed("Brak danych z PSE.")

        factor = 4 if res == RESOLUTION_15M else 1
        prices_today = [float(x["rce_pln"]) for x in raw_today]
        
        prices_tomorrow = []
        if dt_util.now().hour >= 13:
            raw_tomorrow = await self._fetch_day_data(1)
            if raw_tomorrow:
                prices_tomorrow = [float(x["rce_pln"]) for x in raw_tomorrow]

        # --- NOWA LOGIKA: AGREGACJA DO 1H ---
        # Jeśli tryb to nie 15M (czyli 1h), uśredniamy co 4 wartości
        if res != RESOLUTION_15M and len(prices_today) == 96:
            hourly_prices = []
            for i in range(0, 96, 4):
                avg_h = mean(prices_today[i:i+4])
                hourly_prices.extend([round(avg_h, 2)] * 4)
            prices_today = hourly_prices

        if res != RESOLUTION_15M and len(prices_tomorrow) == 96:
            hourly_prices_tom = []
            for i in range(0, 96, 4):
                avg_h = mean(prices_tomorrow[i:i+4])
                hourly_prices_tom.extend([round(avg_h, 2)] * 4)
            prices_tomorrow = hourly_prices_tom
        # --- KONIEC LOGIKI AGREGACJI ---

        full_mask = [False] * len(prices_today)
        
        if price_mode == "ALWAYS ON":
            full_mask = [True] * len(prices_today)
        else:
            try:
                start_h, end_h = map(int, peak_range_str.split("-"))
                start_idx = max(0, start_h * 4) # Zawsze * 4 bo operujemy na masce 96
                end_idx = min(len(prices_today), end_h * 4)
            except Exception:
                start_idx, end_idx = 0, len(prices_today)

            filtered_prices = prices_today[start_idx:end_idx]
            temp_mask = [False] * len(filtered_prices)

            if filtered_prices:
                if price_mode == "LOW PRICE CUTOFF":
                    active_mode = options.get(CONF_OPERATION_MODE, "comfort").lower()
                    p_val = options.get(f"{active_mode}_percentile", 30) / 100.0
                    w_val = options.get(f"{active_mode}_min_window", 2) * 4
                    threshold = sorted(filtered_prices)[int(len(filtered_prices) * p_val)]
                    mask = [p <= threshold for p in filtered_prices]
                    temp_mask = self._apply_min_window(mask, w_val)

                elif price_mode == "CHEAPEST CONSECUTIVE RANGES":
                    count = options.get("consecutive_ranges_count", 4) * (4 if res != RESOLUTION_15M else 1)
                    if len(filtered_prices) >= count:
                        min_sum, best_start = float('inf'), 0
                        for i in range(len(filtered_prices) - count + 1):
                            curr_sum = sum(filtered_prices[i : i + count])
                            if curr_sum < min_sum:
                                min_sum, best_start = curr_sum, i
                        for i in range(best_start, best_start + count): temp_mask[i] = True

                elif "NOT CONSECUTIVE" in price_mode:
                    count = options.get("cheapest_not_consecutive_count", 4) * (4 if res != RESOLUTION_15M else 1)
                    indexed = sorted(enumerate(filtered_prices), key=lambda x: x[1])
                    for i in range(min(count, len(filtered_prices))): temp_mask[indexed[i][0]] = True

            for i, val in enumerate(temp_mask): 
                if start_idx + i < len(full_mask):
                    full_mask[start_idx + i] = val

        return {
            "raw_today": raw_today,
            "price_mode": price_mode,                                         
            "operation_mode": operation_mode,
            "peak_range" : peak_range_str,
            "prices_today": prices_today,
            "prices_tomorrow": prices_tomorrow,
            "stats": {
                "average": round(mean(prices_today), 2) if prices_today else 0,
                "min": min(prices_today) if prices_today else 0,
                "max": max(prices_today) if prices_today else 0,
                "median": round(median(prices_today), 2) if prices_today else 0,
            },
            "cheap_mask": full_mask,
            "resolution": res,
        }

    def _apply_min_window(self, mask, min_len):
        result = mask[:]
        start = None
        for i, val in enumerate(mask + [False]):
            if val and start is None: start = i
            elif not val and start is not None:
                if i - start < min_len:
                    for j in range(start, min(i, len(result))): result[j] = False
                start = None
        return result

def get_current_index(data):
    now = dt_util.now()
    return now.hour * 4 + (now.minute // 15)

class RCESensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True
    _attr_translation_key = "electricity_market_price"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_electricity_market_price"
        self.entity_id = "sensor.rce_electricity_market_price"
        self._attr_native_unit_of_measurement = f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}"

    @property
    def native_value(self):
        prices = self.coordinator.data.get("prices_today", [])
        idx = get_current_index(self.coordinator.data)
        if prices and 0 <= idx < len(prices):
            return prices[idx]
        return None

    @property
    def extra_state_attributes(self):
        stats = self.coordinator.data.get("stats", {})
        return {
            "price_mode": self.coordinator.data.get("price_mode"),                               
            "operation_mode": self.coordinator.data.get("operation_mode"),
            "peak_range": self.coordinator.data.get("peak_range"),                           
            "cheap_mask": self.coordinator.data.get("cheap_mask"),                                   
            "average": stats.get("average"),
            "min": stats.get("min"),
            "max": stats.get("max"),
            "median": stats.get("median"),
            "prices_today": self.coordinator.data.get("prices_today"),
            "prices_tomorrow": self.coordinator.data.get("prices_tomorrow"),
        }

class RCENextCheapWindowSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "next_cheap_window"
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_next_cheap_window"
        self.entity_id = "sensor.rce_next_cheap_window"
    @property
    def native_value(self):
        mask = self.coordinator.data.get("cheap_mask", [])
        idx = get_current_index(self.coordinator.data)
        for i in range(idx + 1, len(mask)):
            if mask[i]: return f"{i // 4:02d}:{(i % 4) * 15:02d}"
        return "N/A"

class RCECheapestPriceTodaySensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True
    _attr_translation_key = "cheapest_price_today"
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_cheapest_price_today"
        self.entity_id = "sensor.rce_cheapest_price_today"
        self._attr_native_unit_of_measurement = f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}"
    @property
    def native_value(self): return self.coordinator.data.get("stats", {}).get("min")

class RCECheapestHourTomorrowSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "cheapest_hour_tomorrow" 
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_cheapest_hour_tomorrow"
        self.entity_id = "sensor.rce_cheapest_hour_tomorrow"
    @property
    def native_value(self):
        prices = self.coordinator.data.get("prices_tomorrow")
        if not prices: return "N/A"
        idx = prices.index(min(prices))
        return f"{idx // 4:02d}:{(idx % 4) * 15:02d}"
