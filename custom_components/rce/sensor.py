"""Platform for sensor integration."""
from __future__ import annotations
import csv
#import locale
#import asyncio
from statistics import mean, median
from zoneinfo import ZoneInfo

import requests
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
#from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from datetime import datetime, timedelta, timezone
from .const import DOMAIN, SCAN_INTERVAL, DEFAULT_CURRENCY, DEFAULT_PRICE_TYPE

URL = "https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/data/{day}"
SENTINEL = object()
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Konfiguracja za pomcą przepływu konfiguracji."""
    
    """This one is in use"""
    async_add_entities([RCESensor()])


class RCESensor(SensorEntity):
    "Sensors data"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = None
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self) -> None:
        _LOGGER.info("RCE sensor")
        super().__init__()
        self.pse_response = None
        self.last_network_pull = datetime(
            year=2000, month=1, day=1, tzinfo=timezone.utc
        )

        # Values for the day
        self._average = None
        self._max = None
        self._min = None
        self._mean = None
        self._off_peak_1 = None
        self._off_peak_2 = None
        self._peak = None

        # Price by current hour.
        self._current_price = None


    def _update(self, today: list):
        """Set attrs"""

        if not today:
            _LOGGER.debug("No data for today, unable to set attrs")
            return False

        self._average = mean(today)
        self._min = min(today)
        self._max = max(today)
        self._off_peak_1 = mean(today[0:8])
        self._off_peak_2 = mean(today[20:])
        self._peak = mean(today[8:20])
        self._mean = median(today)
        
    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def icon(self) -> str:
        return "mdi:currency-eur"

    @property
    def unique_id(self):
        return "rce_pse_pln"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
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
        self._current_price = today[hour]

        return self._current_price
    
#    @property
#    def native_value(self, today):
#        """Return the value reported by the sensor."""
#        return self._update_current_price(today)
    
    async def sday(self, dday: int):
        """fetch day data"""
        now = datetime.now() + timedelta(days=dday)
        try:
#            self.pse_response = await requests.get(
#                f"https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/data/{now.strftime('%Y%m%d')}",
#                timeout=10,
#            )
#            url = f"https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/data/{now.strftime('%Y%m%d')}"
            self.pse_response = await self.hass.async_add_executor_job(requests.get, URL.format(now.strftime('%Y%m%d'))) 
    
            if self.pse_response is None or self.pse_response.status_code != 200:
                return False
    
            return csv.reader(self.pse_response.text.splitlines(), delimiter=";")
    
        except requests.exceptions.ReadTimeout:
            self.pse_response = ""
    
    async def csv_to_day(self, dday: int) -> list:
        """Transform csv to sensor"""
      
        csv_reader = await self.sday(dday)
        if csv_reader: 
            data_pse = []
            for row in csv_reader:
                if not row[1].isnumeric():
                    continue
                data_pse.append(
    				float(row[2].replace(',','.')),
                )
            if not data_pse:
                _LOGGER.debug("No data for a day, unable to set attrs")
                return False
            
            return data_pse
    
    async def csv_to_day_row(self, dday: int) -> list:
        """Transform csv to sensor"""
       
        now = datetime.now()
        csv_reader = await self.sday(dday)
        if csv_reader: 
            now = now.replace(minute=0).replace(second=0) + timedelta(days=dday)
            data_pse = []
            for row in csv_reader:
                if not row[1].isnumeric():
                    continue
                i = {
                    "start" : now.replace(hour=int(row[1])-1),
                    "end" : now.replace(hour=int(row[1])-1,minute=59,second=59),
                    "value": float(row[2].replace(',','.')),
                }
                data_pse.append(i)
            return data_pse

    async def csv_to_time(self, dday: int) -> list:
        """Transform csv to sensor"""
       
        now = datetime.now()
        csv_reader = await self.sday(dday)
        if csv_reader: 
            now = now.replace(minute=0).replace(second=0) + timedelta(days=dday)
            data_pse = []
            for row in csv_reader:
                if not row[1].isnumeric():
                    continue
                data_pse.append(
    				 now.replace(hour=int(row[1])-1).strftime('%Y-%m-%d %H:%M:%S'),
                )

            if not data_pse:
                _LOGGER.debug("No data for a day, unable to set attrs")
                return False
            
            return data_pse
    
    async def async_update(self):
        """Retrieve latest state."""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
#        if now < self.last_network_pull + timedelta(minutes=30):
        if now.strftime('%H') == self.last_network_pull.strftime('%H'):
            return
        self.last_network_pull = now
        self.pse_response = None
        today = await self.csv_to_day(0)
        self._update(today)
        self._attr_native_value = self._update_current_price(today)
        self._attr_extra_state_attributes = {
            "average": self._average,
            "off_peak_1": self._off_peak_1,
            "off_peak_2": self._off_peak_2,
            "peak": self._peak,
            "min": self._min,
            "max": self._max,
            "mean": self._mean,
            "unit": self.unit,
            "currency": DEFAULT_CURRENCY, 
            "today": today,
            "tomorrow": await self.csv_to_day(1),
            "start_time_today": await self.csv_to_time(0),
            "start_time_tomorrow": await self.csv_to_time(1),
            "row_today": await self.csv_to_day_row(0),
            "row_tomorrow": await self.csv_to_day_row(1),
        }
