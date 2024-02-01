# Euribor rates for Home Assistant

## What is it?

A custom component that integrates with euribor-rates.eu to retrieve information about different Euribor rates.

## Installation

### With HACS

1. Add this repository to HACS custom repositories
2. Search for Euribor rates in HACS and install with type integration
3. Restart Home Assistant
4. Enter your account credentials and configre other settings as you wish

### Manual

1. Download source code from latest release tag
2. Copy custom_components/euribor_rates folder to your Home Assistant installation's config/custom_components folder.
3. Restart Home Assistant
4. Configure the integration by adding a new integration in settings/integrations page of Home Assistant

### Integration settings

| Name                         | Type    | Requirement  | Description                                          | Default             |
| ---------------------------- | ------- | ------------ | ---------------------------------------------------- | ------------------- |
| days                         | int     | **Required** | Number of days to retrieve                           | 30                  |
| maturity                     | string  | **Required** | Maturity of rates to retrieve (1 week, 1 month, 3 months, 6 months or 12 months) | 1 week               |

### State attributes

This integration returns the latest Euribor rate as the sensor state. It also returns the following state attributes.

| Name                         | Type    | Description                                          |
| ---------------------------- | ------- | ---------------------------------------------------- |
| latest_rate                  | float   | Latest Euribor rate for selected maturity of the sensor                |
| latest_date                  | date    | Date of the latest Euribor rate                          |
| maturity                     | string  | Selected maturity of the sensor                             |
| history                      | [{date: date, rate: float}]| An array of Euribor rates for the selected maturity of the sensor, for a time period set with days-setting (latest rate and X days before that) |

### Usage with apexcharts-card

One use case for this integration could be to show Euribor rates with [apexcharts-card](https://github.com/RomRider/apexcharts-card).

Below is an example configuration for showing rates for Euribor 12 months, for a time period of one year. As an example, annotation are in place for some days. You could higlight for example the dates when the interest rate of a loan gets updated.

![euribor](https://user-images.githubusercontent.com/54674286/227618468-a86f770a-8d83-4e5d-a05c-8b06abfb1f39.png)

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
