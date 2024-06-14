# homeassistant-rce
Rynkowa cena energii elektrycznej (RCE)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs) 
[![usage_badge](https://img.shields.io/badge/dynamic/json?style=for-the-badge&label=Usage&query=rce.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io) 
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=rce)  

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

You can install the plugin via HACS using the following steps

1. Open HACS
2. Click Integrations
3. Clik the three dots on the top right
4. Click "Custom repositories"
5. Add https://github.com/jacek2511/ha_rce/ and a category of your choice
