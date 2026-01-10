[![GitHub Latest Release][releases_shield]][latest_release] [![License][license-shield]](LICENSE) [![GitHub All Releases][downloads_total_shield]][releases] [![GH-last-commit][latest_commit]][commits] [![HACS][hacsbadge]][hacs]
<!-- [![usage_badge](https://img.shields.io/badge/dynamic/json?label=Usage&query=ha_rce.total&url=https://analytics.home-assistant.io/custom_integrations.json)](https://analytics.home-assistant.io) -->


# homeassistant-rce
**Rynkowa cena energii elektrycznej (RCE)**

Overview
This integration allows for smart device automation based on Polish RCE (Balancing Market) electricity prices published by PSE. The system analyzes price data to identify "Cheap Windows," helping you minimize energy costs.

⚙️ Configuration & Time Resolution
In the integration settings, you can choose how the system handles time intervals:

15 minutes (RCE): Native resolution. Prices change every 15 minutes (96 data points per day).

1 hour (Averaged): The system calculates an average price for each hour. Best for devices that should avoid frequent cycling (e.g., heat pumps, compressors).

📊 Price Calculation Modes (Price Mode)
These modes define the core logic used to identify the "Cheap Window" based on your preferences:

LOW PRICE CUTOFF: The most popular mode. It calculates a price threshold based on a percentile (e.g., the cheapest 30% of the day). If the current price is below this threshold, the window is active.

CHEAPEST CONSECUTIVE RANGES: Ideal for appliances that need to run uninterrupted (like a dishwasher or washing machine). It searches for the single cheapest continuous block of time of a specified length (e.g., the cheapest 3-hour block).

CHEAPEST NOT CONSECUTIVE: Perfect for battery charging or EV charging. It selects a specific number of the cheapest intervals throughout the day, even if they are scattered at different times.

ALWAYS ON (FORCE ON): Overrides all logic and marks every interval as "Cheap." Use this when you need to bypass the price automation and run your devices immediately.

📈 Operation Modes
These profiles determine how "aggressively" the system identifies low-price periods in Low Price Cutoff mode:

Aggressive: Targets only the extreme lows (bottom 10-15% of prices). Maximum savings, shortest runtime.

Super Eco: Highly efficient, focuses on the lowest daily rates.

Eco: Balanced energy-saving mode.

Comfort: Wider operating windows, ensuring stability while maintaining low costs.

📊 ApexCharts Visualization
To see real-time prices and cheap windows on your dashboard, use the following ApexCharts code:
```
type: custom:apexcharts-card
update_interval: 10sec
cache: false
header:
  show: true
  title: Rynek RCE (15-min)
  show_states: true
  colorize_states: true
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Teraz
apex_config:
  stroke:
    dashArray:
      - 0
      - 5
      - 0
      - 0
yaxis:
  - decimals: 0
    min: 0
    apex_config:
      tickAmount: 5
series:
  - entity: sensor.rce_electricity_market_price
    name: Cena aktualna
    type: area
    color: "#2196f3"
    stroke_width: 2
    data_generator: |
      return entity.attributes.prices_today.map((price, index) => {
        return [new Date().setHours(0,0,0,0) + (index * 15 * 60 * 1000), price];
      });
  - entity: sensor.rce_electricity_market_price
    name: Średnia dziś
    type: line
    color: "#9e9e9e"
    stroke_width: 2
    data_generator: |
      const avg = entity.attributes.average;
      return entity.attributes.prices_today.map((_, index) => {
        return [new Date().setHours(0,0,0,0) + (index * 15 * 60 * 1000), avg];
      });
  - entity: sensor.rce_electricity_market_price
    name: Tanie okno (Tryb)
    type: column
    color: "#4caf50"
    opacity: 0.3
    stroke_width: 2
    show:
      in_header: false
      legend_value: false
    group_by:
      func: max
      duration: 15m
    data_generator: |
      const mask = entity.attributes.cheap_mask;
      const prices = entity.attributes.prices_today;
      if (!mask || !prices) return [];
      return prices.map((price, index) => {
        const isCheap = String(mask[index]).toLowerCase() === 'true';
        return [
          new Date().setHours(0,0,0,0) + (index * 15 * 60 * 1000), 
          isCheap ? price : 0
        ];
      });
  - entity: sensor.rce_electricity_market_price
    name: Cena jutro
    type: line
    color: "#ff9800"
    stroke_width: 2
    extend_to: false
    show:
      in_header: false
    data_generator: >
      if (!entity.attributes.prices_tomorrow ||
      entity.attributes.prices_tomorrow.length === 0) return [];

      return entity.attributes.prices_tomorrow.map((price, index) => {
        return [new Date().setHours(0,0,0,0) + ((index + 96) * 15 * 60 * 1000), price];
      });
  - entity: sensor.rce_electricity_market_price
    attribute: operation_mode
    show:
      in_chart: false
      in_header: false
```

🎮 Quick Control: Mode Selection Buttons
You can add a button panel to your Dashboard that allows you to change your energy-saving strategy with a single click.

Mode Capabilities:
FORCE ON (Always On Mode): Ignores prices and forces the device to operate.

AGGRESSIVE: Operates only during absolute price minimums (peak cheap energy periods).

SUPER ECO / ECO: Intermediate energy-saving profiles.

COMFORT: Prioritizes device operation while maintaining a reasonable price.

💻 Button Card Code (Grid + Button)
You can use a standard Grid card with buttons. Paste the following code into the card's YAML editor:
```
type: horizontal-stack
cards:
  - show_name: true
    show_icon: true
    type: button
    name: SUPER ECO
    icon: mdi:sprout
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: super_eco
    card_mod:
      style: |
        ha-state-icon {
          {% if is_state_attr('sensor.rce_electricity_market_price', 'operation_mode', 'super_eco') and is_state_attr('sensor.rce_electricity_market_price', 'current_mode', 'LOW PRICE CUTOFF') %}
            color: #4caf50 !important;
            filter: drop-shadow(0 0 5px #4caf50);
          {% else %}
            color: var(--secondary-text-color);
          {% endif %}
        }
  - show_name: true
    show_icon: true
    type: button
    name: ECO
    icon: mdi:leaf
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: eco
    card_mod:
      style: |
        ha-state-icon {
          {% if is_state_attr('sensor.rce_electricity_market_price', 'operation_mode', 'eco') and is_state_attr('sensor.rce_electricity_market_price', 'current_mode', 'LOW PRICE CUTOFF') %}
            color: #8bc34a !important;
            filter: drop-shadow(0 0 5px #8bc34a);
          {% else %}
            color: var(--secondary-text-color);
          {% endif %}
        }
  - show_name: true
    show_icon: true
    type: button
    name: Komfort
    icon: mdi:home-thermometer
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: comfort
    card_mod:
      style: |
        ha-state-icon {
          {% if is_state_attr('sensor.rce_electricity_market_price', 'operation_mode', 'comfort') and is_state_attr('sensor.rce_electricity_market_price', 'current_mode', 'LOW PRICE CUTOFF') %}
            color: #2196f3 !important;
            filter: drop-shadow(0 0 5px #2196f3);
          {% else %}
            color: var(--secondary-text-color);
          {% endif %}
        }
  - show_name: true
    show_icon: true
    type: button
    name: Agresywny
    icon: mdi:lightning-bolt
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: aggressive
    card_mod:
      style: |
        ha-state-icon {
          {% if is_state_attr('sensor.rce_electricity_market_price', 'operation_mode', 'aggressive') and is_state_attr('sensor.rce_electricity_market_price', 'current_mode', 'LOW PRICE CUTOFF') %}
            color: #ff5722 !important;
            filter: drop-shadow(0 0 5px #ff5722);
          {% else %}
            color: var(--secondary-text-color);
          {% endif %}
        }
  - show_name: true
    show_icon: true
    type: button
    name: Wymuś ON
    icon: mdi:power-plug
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: ALWAYS ON
    card_mod:
      style: |
        ha-state-icon {
          {% if is_state_attr('sensor.rce_electricity_market_price', 'current_mode', 'ALWAYS ON') %}
            color: #ffeb3b !important;
            filter: drop-shadow(0 0 5px #ffeb3b);
          {% else %}
            color: var(--secondary-text-color);
          {% endif %}
        }
```

# Install

### Using [HACS](https://hacs.xyz/) (recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jacek2511&repository=ha_rce&category=Integration)

You can install the plugin via HACS using the following steps

1. Open HACS
2. Click Integrations
3. Clik the three dots on the top right
4. Click "Custom repositories"
5. Add https://github.com/jacek2511/ha_rce/ and a category of your choice

# Configuration
All integration settings are available in the options in the integration configuration panel.

# Available components

### Binary Sensor
* rce_low_price

### Sensors
* rce_cheapest_price_today
* rce_cheapest_hour_tomorrow
* rce_next_cheap_window
* sensor.rce_next_cheap_window

```
  attributes: 
    price_mode - described above 
    operation_mode - described above
    average - average daily energy price
    min - minimum daily energy price
    max - maximum daily energy price
    median - median daily energy price
    peak_range - configurable range of hours for which attributes is calculated
    low_price_cutoff - percentage of average price to set the low price attribute (low_price = hour_price < average * low_price_cutoff)
    prices_today - today's hourly prices in the table []
    prices_tomorrow - tomorrow's hourly prices []
  ```

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[latest_release]: https://github.com/jacek2511/ha_rce/releases/latest
[releases_shield]: https://img.shields.io/github/release/jacek2511/ha_rce.svg?style=popout
[releases]: https://github.com/jacek2511/ha_rce/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/jacek2511/ha_rce/total
[license-shield]: https://img.shields.io/github/license/jacek2511/ha_rce
[latest_commit]: https://img.shields.io/github/last-commit/jacek2511/ha_rce.svg?style=flat-square
[commits]: https://github.com/jack2511/ha_rce/commits/master
