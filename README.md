<!-- [![HACS Default][hacs_shield]][hacs]  -->
[![GitHub Latest Release][releases_shield]][latest_release]
[![License][license-shield]](LICENSE)
[![GitHub All Releases][downloads_total_shield]][releases]
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

[hacs_shield]: https://img.shields.io/static/v1.svg?label=HACS&message=Default&style=popout&color=green&labelColor=41bdf5&logo=HomeAssistantCommunityStore&logoColor=white
[hacs]: https://hacs.xyz/docs/default_repositories
[latest_release]: https://github.com/jacek2511/ha_rce/releases/latest
[releases_shield]: https://img.shields.io/github/release/jacek2511/ha_rce.svg?style=popout
[releases]: https://github.com/jacek2511/ha_rce/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/jacek2511/ha_rce/total
[license-shield]: https://img.shields.io/github/license/jacek2511/ha_rce
