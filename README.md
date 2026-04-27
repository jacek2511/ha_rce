# homeassistant-rce

[![GitHub Latest Release][releases_shield]][latest_release] 
[![License][license-shield]](LICENSE) 
[![GitHub All Releases][downloads_total_shield]][releases] 
[![GH-last-commit][latest_commit]][commits] 
[![HACS][hacsbadge]][hacs]

**Rynkowa cena energii elektrycznej (RCE)** – Integracja dla Home Assistant obsługująca polskie ceny rynkowe publikowane przez PSE.

---

## 📝 Overview
This integration allows for smart device automation based on Polish RCE (Balancing Market) electricity prices. The system analyzes price data to identify **"Cheap Windows"**, helping you minimize energy costs automatically.

### 🆕 What's New
- **Full Tomorrow Support:** Access to prices, cheap windows, and analytics for the next day.
- **Advanced Analytics:** Detection of the **Best cheap window** and **Top 3 cheapest windows** (today & tomorrow).
- **New Sensors:** Dedicated entities for advanced dashboards and automations.
- **Optimized Engine:** Unified window calculation for better performance and consistency.

---

## ⚙️ Configuration & Time Resolution
Settings are available in the integration configuration panel. You can define the time granularity:

* **15 minutes (RCE):** Native resolution. Prices change every 15 minutes (96 data points per day).
* **1 hour (Averaged):** Calculates an average price for each hour. Best for devices that avoid frequent cycling (e.g., heat pumps, compressors).

---

## 📊 Price Calculation Modes
These modes define the logic used to identify "Cheap Windows":

1.  **LOW PRICE CUTOFF:** Calculates a threshold based on a percentile (e.g., the cheapest 30% of the day). Active when the price is below this limit.
2.  **CHEAPEST CONSECUTIVE RANGES:** Searches for the single cheapest continuous block (e.g., 3-hour block). Ideal for dishwashers or washing machines.
3.  **CHEAPEST NOT CONSECUTIVE:** Selects a specific number of the cheapest intervals throughout the day, even if scattered. Perfect for EV/Battery charging.
4.  **ALWAYS ON (FORCE ON):** Overrides logic and marks everything as "Cheap" for immediate manual overrides.

---

## 📈 Operation Modes
Determines how aggressively the system identifies low-price periods (in *Low Price Cutoff* mode):

* **Aggressive:** Targets absolute minimums (bottom 10-15%). Max savings, shortest runtime.
* **Super Eco:** Highly efficient, focuses on the lowest daily rates.
* **Eco:** Balanced energy-saving mode.
* **Comfort:** Wider operating windows for stability and convenience.

---

## 🧩 Available Components

### 🟢 Binary Sensors
* `binary_sensor.rce_low_price`
* `binary_sensor.tomorrow_data_available`

### 📊 Sensors
| Category | Entity ID |
| :--- | :--- |
| **Core** | `sensor.rce_electricity_market_price`, `sensor.rce_next_price` |
| **Today** | `sensor.rce_cheapest_price_today`, `sensor.rce_next_cheap_window`, `sensor.rce_best_window_today`, `sensor.rce_top3_windows_today` |
| **Tomorrow** 🆕 | `sensor.rce_cheapest_hour_tomorrow`, `sensor.rce_next_cheap_window_tomorrow`, `sensor.rce_best_window_tomorrow`, `sensor.rce_top3_windows_tomorrow` |
| **Diagnostics** | `sensor.rce_api_status`, `sensor.rce_last_successful_update` |

---

## 🔍 Sensor Attributes: `sensor.rce_electricity_market_price`

### Core Attributes
* `price_mode` / `operation_mode` – Current settings.
* `average` / `min` / `max` / `median` – Daily statistics.
* `prices_today` / `prices_tomorrow` – Full price arrays.
* `cheap_mask_today` / `cheap_mask_tomorrow` – Boolean arrays for automations.

### 🟢 Window Analytics
* **Best Window:** `avg_price`, `min_price`, `max_price`, `duration_slots`, `savings_vs_avg_day`.
* **Top 3 Windows:** List of 3 best ranges with their respective stats.
* **Next Cheap Window:** `cheap_window_available`, `duration_minutes`, `start_price`, `avg_price`.

---

## 🚀 Installation

### Using [HACS](https://hacs.xyz/) (Recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jacek2511&repository=ha_rce&category=Integration)

1. Open **HACS**.
2. Click **Integrations**.
3. Click the three dots (top right) -> **Custom repositories**.
4. Add `https://github.com/jacek2511/ha_rce/` with category **Integration**.
5. Restart Home Assistant.

---

## 🖼️ Dashboard Visualization

### ApexCharts Price Graph
```yaml
type: custom:apexcharts-card
update_interval: 5min
header:
  show: true
  title: Rynek RCE - Dzisiaj
  show_states: true
  colorize_states: true
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Teraz
series:
  - entity: sensor.rce_electricity_market_price
    name: Minimalna
    show:
      in_chart: false
      in_header: true
    transform: return entity.attributes.min;  
  - entity: sensor.rce_electricity_market_price
    name: Aktualna
    show:
      in_chart: false
      in_header: true
    data_generator: |
      const prices = entity.attributes.prices_today;
      const now = new Date();
      const index = (now.getHours() * 4) + Math.floor(now.getMinutes() / 15);
      return [[now.getTime(), prices[index]]];
  - entity: sensor.rce_electricity_market_price
    name: Maksymalna
    show:
      in_chart: false
      in_header: true
    transform: return entity.attributes.max;
  - entity: sensor.rce_electricity_market_price
    name: Cena aktualna
    type: area
    color: "#2196f3"
    show:
      in_header: false
      hidden_by_default: true
    data_generator: >
      return entity.attributes.prices_today.map((p, i) => [new
      Date().setHours(0,0,0,0) + (i * 15 * 60 * 1000), p]);
  - entity: sensor.rce_electricity_market_price
    name: Średnia
    type: line
    color: "#9e9e9e"
    data_generator: >
      const avg = entity.attributes.average; 
      return entity.attributes.prices_today.map((_, i) => [new
      Date().setHours(0,0,0,0) + (i * 15 * 60 * 1000), avg]);
  - entity: sensor.rce_electricity_market_price
    name: "Tanie okno "
    type: column
    color: "#4caf50"
    opacity: 0.8
    data_generator: |
      const prices = entity.attributes.prices_today;
      const mask = entity.attributes.cheap_mask_today;
      return prices.map((p, i) => {
        const isCheap = String(mask[i]).toLowerCase() === 'true';
        return [new Date().setHours(0,0,0,0) + (i * 15 * 60 * 1000), isCheap ? p : 0];
      });
```

### Quick Control: Mode Selection
```yaml
type: horizontal-stack
cards:
  - type: button
    name: SUPER ECO
    icon: mdi:sprout
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: super_eco
  - type: button
    name: ECO
    icon: mdi:leaf
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: eco
  - type: button
    name: Komfort
    icon: mdi:home-thermometer
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: comfort
  - type: button
    name: Agresywny
    icon: mdi:lightning-bolt
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: LOW PRICE CUTOFF
        mode: aggressive
  - type: button
    name: Wymuś ON
    icon: mdi:power-plug
    tap_action:
      action: call-service
      service: rce.set_operation_mode
      data:
        price_mode: ALWAYS ON
```

---

Oto sformatowany plik `README.md`, zoptymalizowany pod kątem czytelności w repozytorium GitHub:

---

## ⚙️ Configuration

All integration settings are available in the options within the **integration configuration panel**.

---

## 🧩 Available Components

### 🟢 Binary Sensor
* `rce_low_price`
* `tomorrow_data_available`

### 📊 Sensors

| Category | Entity ID |
| :--- | :--- |
| **Core** | `sensor.rce_electricity_market_price`, `sensor.rce_next_price` |
| **Today** | `sensor.rce_cheapest_price_today`, `sensor.rce_next_cheap_window`, `sensor.rce_best_window_today`, `sensor.rce_top3_windows_today` |
| **Tomorrow** 🆕 | `sensor.rce_cheapest_hour_tomorrow`, `sensor.rce_next_cheap_window_tomorrow`, `sensor.rce_best_window_tomorrow`, `sensor.rce_top3_windows_tomorrow` |
| **Diagnostics** | `sensor.rce_api_status`, `sensor.rce_last_successful_update` |

---

## 💡 Notes
> [!IMPORTANT]
> * **Tomorrow data** becomes available only after PSE publishes it.
> * All calculations depend on the selected **Price Mode** and **Operation Mode**.

---

## 🧠 Example Use Cases

* **Optimization:** Run dishwasher in the `best window today`.
* **EV Charging:** Charge EV using `top 3 cheapest windows tomorrow`.
* **Smart Heating:** Heat water only during `cheap mask periods`.
* **Load Shifting:** Delay heavy loads until the `next cheap window`.
 
---

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[latest_release]: https://github.com/jacek2511/ha_rce/releases/latest
[releases_shield]: https://img.shields.io/github/release/jacek2511/ha_rce.svg?style=popout
[releases]: https://github.com/jacek2511/ha_rce/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/jacek2511/ha_rce/total
[license-shield]: https://img.shields.io/github/license/jacek2511/ha_rce
[latest_commit]: https://img.shields.io/github/last-commit/jacek2511/ha_rce.svg?style=flat-square
[commits]: https://github.com/jacek2511/ha_rce/commits/master
