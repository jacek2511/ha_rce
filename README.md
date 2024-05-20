# homeassistant-rce
Rynkowa cena energii elektrycznej (RCE)

This is an integration between Home Assistant and PSE RCE

The RCE sensor provides the current price with today's and tomorrow's prices as attributes. Prices for the next day become available around 3:00 p.m.

<a href="https://github.com/RomRider/apexcharts-card">ApexCharts</a> card is recommended for visualization of the data in Home Assistant.

Example configuration for the cards
<div class="highlight highlight-source-yaml notranslate position-relative overflow-auto" dir="auto" data-snippet-clipboard-copy-content="
type: custom:apexcharts-card
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
      });
">

# Install

You can install the plugin via HACS using the following steps

1. Open HACS
2. Click Integrations
3. Clik the three dots on the top right
4. Click "Custom repositories"
5. Add https://github.com/jacek2511/ha_rce/ and a category of your choice
