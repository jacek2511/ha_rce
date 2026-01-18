from __future__ import annotations

import json
import logging
import requests
from datetime import timedelta
from statistics import mean, median

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import *

_LOGGER = logging.getLogger(__name__)

URL = (
    "https://v2.api.raporty.pse.pl/api/rce-pln"
    "?$filter=business_date eq '{day}'"
    "&$select=dtime,rce_pln"
    "&$orderby=dtime"
)


class RCEDataUpdateCoordinator(DataUpdateCoordinator):
    """Central coordinator for RCE integration."""

    def __init__(self, hass, entry):
        self.entry = entry
        self.last_successful_update: datetime | None = None
        super().__init__(
            hass,
            _LOGGER,
            name="RCE Coordinator",
            update_interval=SCAN_INTERVAL,
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="RCE",
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="JaCeK",
            model="RCE API v2",
        )

    async def _fetch_day(self, offset: int):
        date = (dt_util.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
        try:
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(URL.format(day=date), timeout=20)
            )
            if response.status_code == 200:
                return json.loads(response.text).get("value", [])
        except Exception as err:
            _LOGGER.warning("PSE API error (%s): %s", date, err)
        return []

    # ------------------------------------------------------------
    # MASK LOGIC
    # ------------------------------------------------------------

    def _apply_min_window(self, mask: list[bool], min_len: int) -> list[bool]:
        result = mask[:]
        start = None

        for i, val in enumerate(mask + [False]):
            if val and start is None:
                start = i
            elif not val and start is not None:
                if i - start < min_len:
                    for j in range(start, min(i, len(result))):
                        result[j] = False
                start = None

        return result

    def _calculate_mask(
        self,
        prices: list[float],
        price_mode: str,
        options: dict,
        res: str,
        peak_range: str,
    ) -> list[bool]:

        if not prices:
            return []

        factor = 4
        full_mask = [False] * len(prices)

        include_negative = options.get("negative_prices", False)

        if price_mode == "ALWAYS ON":
            return [True] * len(prices)

        try:
            start_h, end_h = map(int, peak_range.split("-"))
            start_idx = max(0, start_h * factor)
            end_idx = min(len(prices), end_h * factor)
        except Exception:
            start_idx, end_idx = 0, len(prices)

        filtered = prices[start_idx:end_idx]
        temp_mask = [False] * len(filtered)

        if not filtered:
            return full_mask

        # ---- LOW PRICE CUTOFF ----
        if price_mode == "LOW PRICE CUTOFF":
            active_mode = options.get(CONF_OPERATION_MODE, "comfort").lower()
            percentile = options.get(f"{active_mode}_percentile", 30) / 100.0
            min_window = options.get(f"{active_mode}_min_window", 2) * factor

            threshold = sorted(filtered)[int(len(filtered) * percentile)]
            raw_mask = [p <= threshold for p in filtered]
            temp_mask = self._apply_min_window(raw_mask, min_window)

        # ---- CHEAPEST CONSECUTIVE ----
        elif price_mode == "CHEAPEST CONSECUTIVE RANGES":
            count = options.get("consecutive_ranges_count", 4)
            count *= 4 if res != RESOLUTION_15M else 1

            if len(filtered) >= count:
                min_sum = float("inf")
                best_start = 0
                for i in range(len(filtered) - count + 1):
                    s = sum(filtered[i : i + count])
                    if s < min_sum:
                        min_sum = s
                        best_start = i
                for i in range(best_start, best_start + count):
                    temp_mask[i] = True

        # ---- CHEAPEST NOT CONSECUTIVE ----
        elif "NOT CONSECUTIVE" in price_mode:
            count = options.get("cheapest_not_consecutive_count", 4)
            count *= 4 if res != RESOLUTION_15M else 1

            indexed = sorted(enumerate(filtered), key=lambda x: x[1])
            for i in range(min(count, len(filtered))):
                temp_mask[indexed[i][0]] = True

        # ---- NEGATIVE PRICES ----
        if include_negative:
            for i, price in enumerate(filtered):
                if price < 0:
                    temp_mask[i] = True

        # MAPPING TO FULL MASK
        for i, val in enumerate(temp_mask):
            if start_idx + i < len(full_mask):
                full_mask[start_idx + i] = val

        return full_mask

    # ------------------------------------------------------------
    # MAIN UPDATE
    # ------------------------------------------------------------
    
    async def _async_update_data(self):
        try:
            opt = self.entry.options

            res = opt.get(CONF_TIME_RESOLUTION, DEFAULT_TIME_RESOLUTION)
            price_mode = opt.get(CONF_PRICE_MODE, DEFAULT_PRICE_MODE)
            operation_mode = opt.get(CONF_OPERATION_MODE, DEFAULT_OPERATION_MODE)
            peak_range = opt.get(CONF_CUSTOM_PEAK_HOURS_RANGE, "00-24")
            negative_prices = opt.get("negative_prices", False)

            now = dt_util.now()

            if now.hour == 0:
                if self.data:
                    self.data["prices_tomorrow"] = []
                    self.data["cheap_mask_tomorrow"] = []

            # -----------------------
            # TODAY (required)
            # -----------------------
            raw_today = await self._fetch_day(0)
            if not raw_today:
                raise UpdateFailed("No today data from PSE")

            prices_today = [float(x["rce_pln"]) for x in raw_today]

            # -----------------------
            # TOMORROW (optional)
            # -----------------------
            prices_tomorrow: list[float] | None = None
  
            if now.hour >= 13:
                raw_tomorrow = await self._fetch_day(1)
                if raw_tomorrow:
                    prices_tomorrow = [float(x["rce_pln"]) for x in raw_tomorrow]
                else:
                    prices_tomorrow = []

            # -----------------------
            # AGGREGATION 1H
            # -----------------------
            if res != RESOLUTION_15M and len(prices_today) == 96:
                prices_today = [
                    round(mean(prices_today[i:i + 4]), 2)
                    for i in range(0, 96, 4)
                    for _ in range(4)
                ]

            if (
                prices_tomorrow is not None
                and len(prices_tomorrow) == 96
                and res != RESOLUTION_15M
            ):
                prices_tomorrow = [
                    round(mean(prices_tomorrow[i:i + 4]), 2)
                    for i in range(0, 96, 4)
                    for _ in range(4)
                ]

            # -----------------------
            # MASKS
            # -----------------------
            cheap_mask_today = self._calculate_mask(
                prices_today, price_mode, opt, res, peak_range
            )

            cheap_mask_tomorrow = (
                self._calculate_mask(prices_tomorrow, price_mode, opt, res, peak_range)
                if prices_tomorrow
                else []
            )

            # -----------------------
            # SUCCESS
            # -----------------------
            self.last_successful_update = now

            return {
                "api_status": "ok",
                "last_successful_update": now.isoformat(),
                "price_mode": price_mode,
                "operation_mode": operation_mode,
                "peak_range": peak_range,
                "prices_today": prices_today,
                "cheap_mask_today": cheap_mask_today,
                "prices_tomorrow": prices_tomorrow or [],
                "cheap_mask_tomorrow": cheap_mask_tomorrow,
                "resolution": res,
                "stats": {
                    "average": round(mean(prices_today), 2),
                    "min": min(prices_today),
                    "max": max(prices_today),
                    "median": round(median(prices_today), 2),
                },
            }
 
        except Exception as err:
            if self.data is None:
                self.data = {}

            self.data["api_status"] = "error"

            raise UpdateFailed(f"RCE API error: {err}") from err
