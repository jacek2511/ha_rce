"""Platform for sensor integration."""
from __future__ import annotations
import csv
from zoneinfo import ZoneInfo

import requests
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from datetime import datetime, timedelta, timezone

SCAN_INTERVAL = timedelta(seconds=20)
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
        self.cr_time = None
        self.last_update = None
        self.cloud_response = None
        self.last_network_pull = datetime(
            year=2000, month=1, day=1, tzinfo=timezone.utc
        )

        self._hass = hass
        self._attr_force_update = True

        # Price by current hour.
        self._current_price = None

        # Holds the data for today and morrow.
        self._data_today = SENTINEL
        self._data_tomorrow = SENTINEL

        # To control the updates.
        self._last_tick = None

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def icon(self) -> str:
        return "mdi:flash"

    @property
    def unit(self) -> str:
        """Unit"""
        return self._price_type

    @property
    def unit_of_measurement(self) -> str:  # FIXME
        """Return the unit of measurement this sensor expresses itself in."""
        _currency = self._currency
        if self._use_cents is True:
            # Convert unit of measurement to cents based on chosen currency
            _currency = _CURRENTY_TO_CENTS[_currency]
        return "%s/%s" % (_currency, self._price_type)

    @property
    def unique_id(self):
        name = "rce_%s_%s_%s_%s" % (
            self._price_type,
            self._area,
            self._currency,
            self._precision,
        )
        name = name.lower().replace(".", "")
        return name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }
  
    @property
    def today(self):
        """fetch today data"""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
        try:
            self.cloud_response = requests.get(
                f"https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/data/{now.strftime('%Y%m%d')}",
                timeout=10,
            )
            self.cloud_response.encoding = 'ISO-8859-2'

        except ReadTimeout:
            self.cloud_response = ""

    @property
    def tomorrow(self):
        """fetch tomorrow data"""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone)) + timedelta(days=1)
        try:
            self.cloud_response = requests.get(
                f"https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/data/{now.strftime('%Y%m%d')}",
                timeout=10,
            )
            self.cloud_response.encoding = 'ISO-8859-2'
        except requests.exceptions.ReadTimeout:
            self.cloud_response = ""

