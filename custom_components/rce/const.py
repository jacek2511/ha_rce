"""Constants for the RCE (PSE) integration."""

from datetime import timedelta
from typing import Final
import logging

# =========================================================
# DOMAIN & LOGGER
# =========================================================
DOMAIN: Final = "rce"
_LOGGER = logging.getLogger(__name__)

# =========================================================
# GENERAL SETTINGS
# =========================================================
SCAN_INTERVAL = timedelta(minutes=15)

DEFAULT_CURRENCY: Final = "PLN"
DEFAULT_PRICE_TYPE: Final = "MWh"

# =========================================================
# TIME RESOLUTION
# =========================================================
CONF_TIME_RESOLUTION: Final = "time_resolution"
RESOLUTION_15M: Final = "15m"
RESOLUTION_1H: Final = "1h"

DEFAULT_TIME_RESOLUTION: Final = RESOLUTION_15M

# =========================================================
# CONFIGURATION KEYS (Options Flow)
# =========================================================
CONF_PRICE_MODE: Final = "price_mode"
CONF_OPERATION_MODE: Final = "operation_mode"
CONF_CUSTOM_PEAK_HOURS_RANGE: Final = "custom_peak_hours_range"
CONF_NEGATIVE_PRICES: Final = "negative_prices"

# Klucze dla suwaków trybów ilościowych
CONF_CONSECUTIVE_COUNT: Final = "consecutive_ranges_count"
CONF_NOT_CONSECUTIVE_COUNT: Final = "cheapest_not_consecutive_count"

# =========================================================
# DEFAULTS
# =========================================================
DEFAULT_PRICE_MODE: Final = "LOW PRICE CUTOFF"
DEFAULT_OPERATION_MODE: Final = "comfort"
DEFAULT_CUSTOM_PEAK_HOURS_RANGE: Final = "00-24"
DEFAULT_NEGATIVE_PRICES: Final = True

# =========================================================
# OPERATION MODES (Presets dla Low Price Cutoff)
# =========================================================
MODE_SUPER_ECO = "super_eco"
MODE_ECO = "eco"
MODE_COMFORT = "comfort"
MODE_AGGRESSIVE = "aggressive"

OPERATION_MODES = [
    MODE_SUPER_ECO,
    MODE_ECO,
    MODE_COMFORT,
    MODE_AGGRESSIVE,
]

# =========================================================
# PRICE MODES
# =========================================================
PRICE_MODE_LOW_PRICE_CUTOFF = "LOW PRICE CUTOFF"
PRICE_MODE_CHEAPEST_CONSECUTIVE = "CHEAPEST CONSECUTIVE RANGES"
PRICE_MODE_CHEAPEST_ANY = "CHEAPEST RANGES (NOT CONSECUTIVE)"
PRICE_MODE_ALWAYS_ON = "ALWAYS ON"

PRICE_MODES = [
    PRICE_MODE_LOW_PRICE_CUTOFF,
    PRICE_MODE_CHEAPEST_CONSECUTIVE,
    PRICE_MODE_CHEAPEST_ANY,
    PRICE_MODE_ALWAYS_ON,
]

# =========================================================
# SENSOR ATTRIBUTES
# =========================================================
ATTR_RESOLUTION = "resolution"
ATTR_PRICE_MODE = "price_mode"
