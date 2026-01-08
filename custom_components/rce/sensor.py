"""Platform for sensor integration."""
from __future__ import annotations

import json
import requests
from statistics import mean, median
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.device_registry import DeviceEntryType

from .const import (
    DOMAIN,
    _LOGGER,
    DEFAULT_CURRENCY,
    DEFAULT_PRICE_TYPE,
    CONF_CUSTOM_PEAK_HOURS_RANGE,
    CONF_LOW_PRICE_CUTOFF,
    DEFAULT_CUSTOM_PEAK_HOURS_RANGE,
    DEFAULT_LOW_PRICE_CUTOFF,
    CONF_NUMBER_OF_CHEAPEST_HOURS,
    DEFAULT_NUMBER_OF_CHEAPEST_HOURS,
    CONF_PRICE_MODE,
    DEFAULT_PRICE_MODE,
    CONF_NEGATIVE_PRICES,
    DEFAULT_NEGATIVE_PRICES,
)

URL = (
    "https://v2.api.raporty.pse.pl/api/rce-pln"
    "?$filter=business_date eq '{day}'"
    "&$select=business_date,dtime,rce_pln"
    "&$orderby=dtime"
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    custom_peak = config_entry.options.get(
        CONF_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_CUSTOM_PEAK_HOURS_RANGE
    )
    low_price_cutoff = (
        config_entry.options.get(
            CONF_LOW_PRICE_CUTOFF, DEFAULT_LOW_PRICE_CUTOFF
        )
        / 100
    )
    cheapest_hours = config_entry.options.get(
        CONF_NUMBER_OF_CHEAPEST_HOURS, DEFAULT_NUMBER_OF_CHEAPEST_HOURS
    )
    price_mode = config_entry.options.get(
        CONF_PRICE_MODE, DEFAULT_PRICE_MODE
    )
    negative_prices = config_entry.options.get(
        CONF_NEGATIVE_PRICES, DEFAULT_NEGATIVE_PRICES
    )

    async_add_entities(
        [
            RCESensor(
                custom_peak,
                low_price_cutoff,
                cheapest_hours,
                price_mode,
                negative_prices,
            )
        ]
    )


class RCESensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True

    def __init__(
        self,
        custom_peak: str,
        low_price_cutoff: float,
        cheapest_hours: int,
        price_mode: str,
        negative_prices: bool,
    ) -> None:
        super().__init__()
        _LOGGER.info("RCE sensor – API v2 (15 min → 1h)")

        self.last_network_pull = datetime(
            year=2000, month=1, day=1, tzinfo=timezone.utc
        )

        self._today = []
        self._tomorrow = []

        self._average = None
        self._min = None
        self._max = None
        self._mean = None
        self._off_peak_1 = None
        self._off_peak_2 = None
        self._peak = None
        self._custom_peak = None
        self._min_average = None
        self._max_cheapest_price = None

        self.custom_peak = custom_peak
        self.low_price_cutoff = low_price_cutoff
        self.cheapest_hours = cheapest_hours
        self.price_mode = price_mode
        self.negative_prices = negative_prices

    # -------------------------------------------------------------

    async def sday(self, dday: int):
        now = datetime.now() + timedelta(days=dday)
        try:
            response = await self.hass.async_add_executor_job(
                requests.get, URL.format(day=now.strftime("%Y-%m-%d"))
            )
            if response.status_code == 200:
                return json.loads(response.text)
        except requests.RequestException:
            _LOGGER.warning("PSE API unreachable")
        return None

    async def json_to_day_raw(self, dday: int) -> list:
        json_data = await self.sday(dday)
        if not json_data or "value" not in json_data:
            return []

        buckets = defaultdict(list)

        for item in json_data["value"]:
            dt = datetime.fromisoformat(item["dtime"])
            buckets[dt.hour].append(float(item["rce_pln"]))

        day = []
        for hour in range(24):
            if hour in buckets:
                day.append(
                    {
                        "hour": hour,
                        "start": f"{hour:02d}:00",
                        "tariff": round(mean(buckets[hour]), 2),
                        "low_price": False,
                    }
                )

        return day

    # -------------------------------------------------------------

    def _update(self, day: list):
        if not day:
            return

        price = [item["tariff"] for item in day]

        self._average = round(mean(price), 2)
        self._min = min(price)
        self._max = max(price)
        self._mean = round(median(price), 2)

        self._off_peak_1 = round(mean(price[0:8]), 2)
        self._peak = round(mean(price[8:20]), 2)
        self._off_peak_2 = round(mean(price[20:]), 2)

        start, end = map(int, self.custom_peak.split("-"))
        self._custom_peak = round(mean(price[start:end]), 2)

    def _low_price_hours(self, day: list):
        price = [item["tariff"] for item in day]

        if self.negative_prices:
            for i, p in enumerate(price):
                if p <= 0:
                    day[i]["low_price"] = True

        if self.price_mode == "LOW PRICE CUTOFF":
            for i, p in enumerate(price):
                if p < self._custom_peak * self.low_price_cutoff:
                    day[i]["low_price"] = True
            self._max_cheapest_price = self._custom_peak * self.low_price_cutoff

        elif self.price_mode == "CHEAPEST CONSECUTIVE HOURS":
            self._min_average = float("inf")
            idx = 0
            for i in range(len(price) - self.cheapest_hours + 1):
                avg = mean(price[i : i + self.cheapest_hours])
                if avg < self._min_average:
                    self._min_average = round(avg, 2)
                    idx = i
            for k in range(self.cheapest_hours):
                day[idx + k]["low_price"] = True
            self._max_cheapest_price = max(
                price[idx : idx + self.cheapest_hours]
            )

        elif self.price_mode == "CHEAPEST HOURS (NOT CONSECUTIVE)":
            cheapest = sorted(day, key=lambda d: d["tariff"])[
                : self.cheapest_hours
            ]
            for item in cheapest:
                item["low_price"] = True
            self._max_cheapest_price = max(
                item["tariff"] for item in cheapest
            )

    # -------------------------------------------------------------

    async def full_update(self):
        self._today = await self.json_to_day_raw(0)
        self._tomorrow = await self.json_to_day_raw(1)

        self._low_price_hours(self._today)
        self._update(self._today)

        now_hour = datetime.now().hour
        self._attr_native_value = self._today[now_hour]["tariff"]

    async def async_update(self):
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
        if now.date() != self.last_network_pull.date():
            await self.full_update()
        self.last_network_pull = now

    # -------------------------------------------------------------

    @property
    def name(self):
        return "Rynkowa Cena Energii Elektrycznej"

    @property
    def unique_id(self):
        return "rce_pse_pln"

    @property
    def unit_of_measurement(self):
        return f"{DEFAULT_CURRENCY}/{DEFAULT_PRICE_TYPE}"

    @property
    def device_info(self):
        return {
            "entry_type": DeviceEntryType.SERVICE,
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": "RCE PSE",
            "manufacturer": "PSE",
        }

    @property
    def extra_state_attributes(self):
        if not self._today:
            return None

        hour = datetime.now().hour
        next_price = (
            self._today[hour + 1]["tariff"]
            if hour < 23
            else self._tomorrow[0]["tariff"]
            if self._tomorrow
            else None
        )

        return {
            "next_price": next_price,
            "average": self._average,
            "min": self._min,
            "max": self._max,
            "mean": self._mean,
            "off_peak_1": self._off_peak_1,
            "peak": self._peak,
            "off_peak_2": self._off_peak_2,
            "custom_peak": self._custom_peak,
            "min_average": self._min_average,
            "max_cheapest_price": self._max_cheapest_price,
            "today": self._today,
            "tomorrow": self._tomorrow,
            "currency": DEFAULT_CURRENCY,
        }
