"""Constants for the RCE integration."""

from datetime import timedelta
import logging

DOMAIN = "rce"
DEFAULT_CURRENCY = "zł"
DEFAULT_PRICE_TYPE = "MWh"
_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
