"""Constants for the RCE integration."""

from datetime import timedelta
from typing import Final

import logging

DOMAIN: Final = "rce"
DEFAULT_CURRENCY: Final = "PLN"
DEFAULT_PRICE_TYPE: Final = "MWh"

DEFAULT_CUSTOM_PEAK_HOURS_RANGE = "10-17"
DEFAULT_LOW_PRICE_CUTOFF = 90

CONF_CUSTOM_PEAK_HOURS_RANGE: Final = "custom_peak_range"
CONF_LOW_PRICE_CUTOFF: Final = "low_price_cutoff"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
