# Euribor rates for Home Assistant

Home Assistant integration for the Euribor rates published by euribor-rates.eu.

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![GitHub Activity][commits-shield]][commits]

## Support

Hey dude! Help me out for a couple of :beers: or a :coffee:!

[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://www.buymeacoffee.com/jesmak)

## What is it?

A custom component that follows the Euribor rates from [euribor-rates.eu](https://www.euribor-rates.eu/). Each
maturity is added separately and gets a sensor whose state is the newest rate, with the rates of the days before it in
the sensor's attributes.

The history in the attributes is what makes it useful with a chart card: see [Usage with
apexcharts-card](#usage-with-apexcharts-card) below.

## Installation

### With HACS

1. Add this repository to HACS custom repositories with type **Integration**
2. Search for Euribor rates in HACS and download it
3. Restart Home Assistant
4. Add the integration in Settings › Devices & services, and choose a maturity

### Manual

1. Download the source code from the latest release
2. Copy the `custom_components/euribor_rates` folder to your Home Assistant installation's `config/custom_components`
   folder
3. Restart Home Assistant
4. Add the integration in Settings › Devices & services, and choose a maturity

## Settings

Add the integration once for each maturity you want to follow. To change how much history a sensor keeps, choose
**Reconfigure** from its menu on the integration page. The maturity itself stays as it is, because the sensor is named
after it.

| Name     | Type   | Description                                                      | Default |
| -------- | ------ | ---------------------------------------------------------------- | ------- |
| Maturity | enum   | `1 week`, `1 month`, `3 months`, `6 months` or `12 months`        |         |
| Days     | number | How far back the rates in the sensor's attributes reach, in days | 30      |

## Sensor

The state is the newest published rate as a percentage. The sensor is named after its maturity, for example
`sensor.euribor_12_months`.

| Attribute       | Description                                             |
| --------------- | ------------------------------------------------------- |
| `latest_rate`   | The newest rate, the same as the state                  |
| `latest_date`   | The day the newest rate was published                   |
| `maturity`      | The maturity the sensor follows                         |
| `history`       | The rates of the days before it, below                  |
| `attribution`   | Data credit                                             |

Each entry in `history` has:

| Key    | Description                    |
| ------ | ------------------------------ |
| `date` | The day, as `YYYY-MM-DD`       |
| `rate` | The rate published that day    |

Rates are published once a day on working days, and the sensor is updated every three hours. The history isn't stored
in the recorder, only the state. The sensor is unavailable while euribor-rates.eu can't be reached.

## Upgrading from 1.x

Nothing needs to be done: the maturity, the sensor, its history and the settings carry over, and entity IDs stay as
they were. The number of days is now changed with **Reconfigure** instead of the options dialog.

### Usage with apexcharts-card

One use for this integration is a chart of the rates with
[apexcharts-card](https://github.com/RomRider/apexcharts-card), drawn from the `history` attribute. Below is a
configuration for the 12 month rate over a year, with annotations marking the days a loan's rate is updated.

![A chart of the Euribor 12 month rate](docs/images/apexcharts.png)

```
type: custom:apexcharts-card
graph_span: 365d
header:
  show: true
  title: Euribor 12 months
  show_states: true
  colorize_states: true
all_series_config:
  curve: straight
apex_config:
  chart:
    height: 150px
  legend:
    show: false
  annotations:
    xaxis:
      - x: 1659928000000 # these have to be timestamps (in milliseconds)
        label:
          style:
            color: '#000'
          text: House
      - x: 1656928000000
        label:
          style:
            color: '#000'
          text: Cabin
      - x: 1651384000000
        label:
          style:
            color: '#000'
          text: Renovation
series:
  - entity: sensor.euribor_12_months
    data_generator: |
      return entity.attributes.history.map((entry) => {
        return [entry["date"], entry["rate"]];
      });
    stroke_width: 1
    float_precision: 3
    yaxis_id: daily
    name: Rate of the day
yaxis:
  - id: daily
    min: -0.5
    max: 5
    apex_config:
      tickAmount: 4
      labels:
        style:
          fontSize: 8px
        formatter: |
          EVAL:function(value) {
            return value.toFixed(1) + ' %'; 
          }
```

## Data

Euribor rates: [euribor-rates.eu](https://www.euribor-rates.eu/).

## Development

Requires Python 3.14.

```
python3.14 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest
.venv/bin/ruff check .
```

| Path                           | What it contains                                      |
| ------------------------------ | ----------------------------------------------------- |
| `__init__.py`                  | Setup                                                 |
| `config_flow.py`               | Choosing the maturity and the length of the history   |
| `api.py`                       | The chart endpoint of euribor-rates.eu                |
| `rates.py`                     | Reading the rates it sends                            |
| `coordinator.py`               | Fetching the rates every three hours                  |
| `sensor.py`                    | The sensor                                            |
| `translations/<language>.json` | Home Assistant UI texts                               |

[commits-shield]: https://img.shields.io/github/commit-activity/y/jesmak/euribor_rates.svg?style=for-the-badge
[commits]: https://github.com/jesmak/euribor_rates/commits/main
[license-shield]: https://img.shields.io/github/license/jesmak/euribor_rates.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jesmak/euribor_rates.svg?style=for-the-badge
[releases]: https://github.com/jesmak/euribor_rates/releases
