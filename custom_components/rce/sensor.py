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
from .const import DOMAIN, _LOGGER, SCAN_INTERVAL, DEFAULT_CURRENCY, DEFAULT_PRICE_TYPE, CONF_CUSTOM_PEAK_HOURS_RANGE, CONF_LOW_PRICE_CUTOFF, DEFAULT_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_LOW_PRICE_CUTOFF, CONF_NUMBER_OF_CHEAPEST_HOURS, DEFAULT_NUMBER_OF_CHEAPEST_HOURS, CONF_PRICE_MODE, DEFAULT_PRICE_MODE 


URL = "https://api.raporty.pse.pl/api/rce-pln?$filter=doba eq '{day}'"
SENTINEL = object()


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Konfiguracja za pomcą przepływu konfiguracji."""

    if config_entry.options.get(CONF_CUSTOM_PEAK_HOURS_RANGE):
        custom_peak = config_entry.options.get(CONF_CUSTOM_PEAK_HOURS_RANGE, DEFAULT_CUSTOM_PEAK_HOURS_RANGE)
    if config_entry.options.get(CONF_LOW_PRICE_CUTOFF):
        low_price_cutoff = config_entry.options.get(CONF_LOW_PRICE_CUTOFF, DEFAULT_LOW_PRICE_CUTOFF) / 100
    if config_entry.options.get(CONF_NUMBER_OF_CHEAPEST_HOURS):
        cheapest_hours = config_entry.options.get(CONF_NUMBER_OF_CHEAPEST_HOURS, DEFAULT_NUMBER_OF_CHEAPEST_HOURS)
    if config_entry.options.get(CONF_PRICE_MODE):
        price_mode = config_entry.options.get(CONF_PRICE_MODE, DEFAULT_PRICE_MODE)

    async_add_entities([RCESensor(custom_peak, low_price_cutoff, cheapest_hours, price_mode)])


class RCESensor(SensorEntity):
    "Sensors data"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = None
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True

    def __init__(self, custom_peak: str, low_price_cutoff: int, cheapest_hours: int, price_mode: str) -> None:
        """Initialize Forecast.Solar sensor."""
        _LOGGER.info("RCE sensor")
        super().__init__()

        self.pse_response = None
        self.last_network_pull = datetime(year=2000, month=1, day=1, tzinfo=timezone.utc)

        # Values for the day
        self._today = None
        self._tomorrow = None
        self._next_price = None
        self._average = None
        self._max = None
        self._min = None
        self._mean = None
        self._off_peak_1 = None
        self._off_peak_2 = None
        self._peak = None
        self._min_average = None
        self._custom_peak = None
        self.custom_peak = custom_peak
        self.low_price_cutoff = low_price_cutoff
        self.cheapest_hours = cheapest_hours
        self.price_mode = price_mode

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
# MODE: LOW PRICE CUTOFF
        if self.price_mode == 'LOW PRICE CUTOFF':
            for i, price_hour in enumerate(price):
                if price_hour < self._custom_peak * self.low_price_cutoff:
                    day[i]['low_price'] = True

# MODE: CHEAPEST CONSECUTIVE HOURS
        elif self.price_mode == 'CHEAPEST CONSECUTIVE HOURS':
            self._min_average = float('inf')
            min_average_index = 0
            for i in range(len(price)):
                current_average = mean(price[i:i + self.cheapest_hours])
                if current_average < self._min_average:
                    self._min_average = round(current_average, 2)
                    min_average_index = i
                if i + self.cheapest_hours == len(price):
                    for k in range (self.cheapest_hours): 
                        day[min_average_index + k]['low_price'] = True
                    return
# MODE: CHEAPEST HOURS (NOT CONSECUTIVE)
        elif self.price_mode == 'CHEAPEST HOURS (NOT CONSECUTIVE)':
            day_copy = sorted(day, key=lambda d: d['tariff'])
            for k in range (self.cheapest_hours): 
                m = day_copy[k]['start'][-5:-3]
                day[int(m)]['low_price'] = True
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

    @property
    def extra_state_attributes(self):
        if self._today:
            attrs =  {
                "next_price": self._update_next_price(self._today, self._tomorrow),
                "average": round(self._average, 2),
                "off_peak_1": round(self._off_peak_1, 2),
                "off_peak_2": round(self._off_peak_2,2),
                "peak": round(self._peak, 2),
                "custom_peak": round(self._custom_peak, 2),
                "min": self._min,
                "max": self._max,
                "mean": round(self._mean, 2),
                "min_average": self._min_average,
                "unit": self.unit,
                "currency": DEFAULT_CURRENCY, 
                "custom_peak_range" : self.custom_peak,
                "low_price_cutoff": self.low_price_cutoff * 100,
                "today": self._today,
                "tomorrow": self._tomorrow,
            }
            return attrs
    
    def _update_current_price(self, today) -> None:
        """update the current price (price this hour)"""
        hour = int(datetime.now().strftime('%H'))
        return today[hour]['tariff']

    def _update_next_price(self, today, tomorrow) -> None:
        """update the next price (price next hour)"""
        if today:
            hour = int(datetime.now().strftime('%H'))
            if hour < 23:
              return today[hour + 1]['tariff']
            else:
              return tomorrow[0]['tariff']
    
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
        self._today = await self.json_to_day_raw(0)
        self._update(self._today)
        self._attr_native_value = self._update_current_price(self._today)
        self._low_price_hours(self._today)
        self._tomorrow = await self.json_to_day_raw(1)
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
        self._attr_native_value = self._update_current_price(self.extra_state_attributes["today"])
        self.last_network_pull = now
        if not self.extra_state_attributes["tomorrow"] and int(now.strftime('%H')) > 14: 
            await self.full_update()
            self.last_network_pull = now
        return
