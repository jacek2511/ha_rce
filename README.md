[![GitHub Latest Release][releases_shield]][latest_release] [![License][license-shield]](LICENSE) [![GitHub All Releases][downloads_total_shield]][releases] [![GH-last-commit][latest_commit]][commits] [![HACS][hacsbadge]][hacs]
<!-- [![usage_badge](https://img.shields.io/badge/dynamic/json?label=Usage&query=ha_rce.total&url=https://analytics.home-assistant.io/custom_integrations.json)](https://analytics.home-assistant.io) -->


# homeassistant-rce
**Rynkowa cena energii elektrycznej (RCE)**

This is an integration between Home Assistant and PSE RCE

The RCE sensor provides the current price with today's and tomorrow's prices as attributes. Prices for the next day become available around 3:00 p.m.

<a href="https://github.com/RomRider/apexcharts-card">ApexCharts</a> card is recommended for visualization of the data in Home Assistant.

Example configuration for the cards
<pre class="wp-block-code"><code>type: custom:apexcharts-card
graph_span: 24h
span:
  start: day
header:
  show: true
  title: Rynkowa Cena Energii Elektrycznej [zł/MWh]
  colorize_states: true
now:
  show: true
  label: Teraz
  color: var(--secondary-color)
yaxis:
  - decimals: 0
    apex_config:
      tickAmount: 5
series:
  - entity: sensor.rynkowa_cena_energii_elektrycznej
    type: column
    name: Cena Rynkowa Energii Elektrycznej
    float_precision: 2
    data_generator: |
      return entity.attributes.today.map((start, index) => {
        return [new Date(start["start"]).getTime(), entity.attributes.today[index]['tariff']];
      });</code></pre>

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
![image](https://github.com/jacek2511/ha_rce/assets/112733566/f9e834b5-1322-435d-9ac3-e15b3b187cb9)

# Available components

### Sensor
* rynkowa_cena_energii_elektrycznej - current energy price

```
  attributes: 
    next_price - energy price in the next hour
    average - average daily energy price
    off_peak_1 - average energy price from 00:00 to 08:00
    off_peak_2 - average energy price from 20:00 to 00:00
    peak - average energy price from 08:00 to 20:00
    min_average - minimum average energy price in the range of x consecutive hours; where x is configurable in options
    custom_peak - average energy price over the range of hours defined by custom_peak_range
    min - minimum daily energy price
    max - maximum daily energy price
    mean - median daily energy price
    custom_peak_range - configurable range of hours for which the custom_peak attribute is calculated
    low_price_cutoff - percentage of average price to set the low price attribute (low_price = hour_price < average * low_price_cutoff)
    today - today's hourly prices in the format
      - start: 2024-06-28 00:00
        tariff: 604.2
        low_price: false
      - start: 2024-06-28 01:00
        tariff: 488.93
        low_price: false
    tomorrow - tomorrow's hourly prices
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
