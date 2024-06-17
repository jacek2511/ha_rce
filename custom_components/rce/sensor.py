"""Platform for sensor integration."""
from __future__ import annotations
import json
import requests
from statistics import mean, median 
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType

from datetime import datetime, timedelta, timezone
from .const import DOMAIN, _LOGGER, SCAN_INTERVAL, DEFAULT_CURRENCY, DEFAULT_PRICE_TYPE, CONF_CUSTOM_PEAK_HOURS_RANGE, CONF_LOW_PRICE_CUTOFF, DEFAULT_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_LOW_PRICE_CUTOFF


URL = "https://api.raporty.pse.pl/api/rce-pln?$filter=doba eq '{day}'"
SENTINEL = object()


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Konfiguracja za pomcą przepływu konfiguracji."""

    if config_entry.options.get(CONF_CUSTOM_PEAK_HOURS_RANGE):
        custom_peak = config_entry.options.get(CONF_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_CUSTOM_PEAK_HOURS_RANGE)
    if config_entry.options.get(CONF_LOW_PRICE_CUTOFF):
        low_price_cutoff = config_entry.options.get(CONF_LOW_PRICE_CUTOFF, DEFAULT_LOW_PRICE_CUTOFF) / 100

    async_add_entities([RCESensor(custom_peak, low_price_cutoff)])


class RCESensor(SensorEntity):
    "Sensors data"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = None
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True

    def __init__(self, custom_peak: str, low_price_cutoff: int) -> None:
        """Initialize Forecast.Solar sensor."""
        _LOGGER.info("RCE sensor")
        super().__init__()

        self.pse_response = None
        self.last_network_pull = datetime(year=2000, month=1, day=1, tzinfo=timezone.utc)

        # Values for the day
        self._average = None
        self._max = None
        self._min = None
        self._mean = None
        self._off_peak_1 = None
        self._off_peak_2 = None
        self._peak = None
        self._custom_peak = None
        self.custom_peak = custom_peak
        self.low_price_cutoff = low_price_cutoff

    def _update(self, day: dict):
        """Set attrs"""

        if not day:
            _LOGGER.debug("No data for today, unable to set attrs")
            return
        price = []
        price = (([item['tariff'] for item in day]))

        self._average = round(mean(price), 2)
        self._min = min(price)
        self._max = max(price)
        self._off_peak_1 = round(mean(price[0:8]), 2)
        self._off_peak_2 = round(mean(price[20:]), 2)
        self._peak = round(mean(price[8:20]), 2)
        self._mean = round(median(price), 2)
        self._custom_peak = round(mean(price[int(self.custom_peak.split("-")[0]):int(self.custom_peak.split("-")[1])]), 2)

    def _low_price_hours(self, day: dict):

        price = []
        price = (([item['tariff'] for item in day]))
        for i, price_hour in enumerate(price):
            if price_hour < self._custom_peak * self.low_price_cutoff:
                day[i]['low_price'] = True
        return
    
    @property
    def name(self) -> str:
        return "Rynkowa Cena Energi Elektrycznej"

    @property
    def icon(self) -> str:
        return "mdi:currency-eur"

    @property
    def unique_id(self):
        return "rce_pse_pln"

    @property
    def device_info(self):
        return {
            "entry_type": DeviceEntryType.SERVICE,
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": "Rynkowa Cena Energii Elektrycznej",
            "manufacturer": "PSE.RCE",
        }

    @property
    def unit(self) -> str:
        """Unit"""
        return DEFAULT_PRICE_TYPE

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%s/%s" % (DEFAULT_CURRENCY, DEFAULT_PRICE_TYPE)

    def _update_current_price(self, today) -> None:
        """update the current price (price this hour)"""
        hour = int(datetime.now().strftime('%H'))
        return today[hour]['tariff']

    
    async def sday(self, dday: int):
        """fetch day data"""
        now = datetime.now() + timedelta(days=dday)
        try:
            self.pse_response = await self.hass.async_add_executor_job(requests.get, URL.format(day=now.strftime('%Y-%m-%d'))) 

            if self.pse_response.status_code == 200:
                return json.loads(self.pse_response.text)
            else:
                return False

        except requests.exceptions.ReadTimeout:
            self.pse_response = None

    
    async def json_to_day_raw(self, dday: int) -> list:
        """Transform json to sensor"""
       
        json_data = await self.sday(dday)
        if json_data: 
            data_pse = []
            for item in json_data["value"]:
                if item['udtczas_oreb'].replace(' - ',':').split(':')[1] == "00":
                    i = {
                        "start" : item['doba'] + " " + item['udtczas_oreb'].split(' - ')[0], # + ":00",
                        "tariff" : float(item['rce_pln']),
                        "low_price" : False,
                    }
                    data_pse.append(i)
            if not data_pse:
                _LOGGER.debug("No data for a day, unable to set attrs")

            return data_pse


    async def full_update(self):
        self.pse_response = None
        today = await self.json_to_day_raw(0)
        self._update(today)
        self._attr_native_value = self._update_current_price(today)
        self._low_price_hours(today)
        tomorrow = await self.json_to_day_raw(1)
        self._attr_extra_state_attributes = {
            "average": self._average,
            "off_peak_1": self._off_peak_1,
            "off_peak_2": self._off_peak_2,
            "peak": self._peak,
            "custom_peak": self._custom_peak,
            "min": self._min,
            "max": self._max,
            "mean": self._mean,
            "unit": self.unit,
            "currency": DEFAULT_CURRENCY, 
            "custom_peak_range" : self.custom_peak,
            "low_price_cutoff": self.low_price_cutoff * 100,
            "today": today,
            "tomorrow": tomorrow,
        }
        return

    async def async_update(self):
        """Retrieve latest state."""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
        if now.strftime('%d%Y') != self.last_network_pull.strftime('%d%Y'):
            await self.full_update()
            self.last_network_pull = now
            return
        if now.strftime('%H') == self.last_network_pull.strftime('%H'):
            return
        today_price = self._attr_extra_state_attributes["today"]
        self._attr_native_value = self._update_current_price(today_price)
        self.last_network_pull = now
        if not self._attr_extra_state_attributes["tomorrow"] and int(now.strftime('%H')) > 14: 
            await self.full_update()
            self.last_network_pull = now
