"""Constants for the RCE integration."""

from datetime import timedelta
from typing import Final

import logging

DOMAIN: Final = "rce"
DEFAULT_CURRENCY: Final = "PLN"
DEFAULT_PRICE_TYPE: Final = "MWh"

DEFAULT_CUSTOM_PEAK_HOURS_RANGE = "10-17"
DEFAULT_LOW_PRICE_CUTOFF = 90
DEFAULT_NUMBER_OF_CHEAPEST_HOURS = 3
DEFAULT_PRICE_MODE = "LOW PRICE CUTOFF"

CONF_CUSTOM_PEAK_HOURS_RANGE: Final = "custom_peak_range"
CONF_LOW_PRICE_CUTOFF: Final = "low_price_cutoff"
CONF_NUMBER_OF_CHEAPEST_HOURS: Final ="number_of_cheapest_hours"
CONF_PRICE_MODE: Final = "cheapest_price_mode"

PRICE_MODES = [
    "LOW PRICE CUTOFF",
    "CHEAPEST CONSECUTIVE HOURS",
    "CHEAPEST HOURS (NOT CONSECUTIVE)",
]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
