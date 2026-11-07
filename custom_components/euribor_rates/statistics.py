"""Keeping the rates in Home Assistant's long term statistics.

The rates live in the statistics of each maturity's history sensor, which is what
a statistics graph card, or apexcharts with `statistics: { type: mean, period: day }`,
reads. That sensor has no state class and a date for its state, so the recorder
never compiles statistics of its own for it and nothing but the rates written here
ends up there. (The rate sensor keeps its state class, and the recorder's
statistics of it follow what it showed: a rate a day or two old, since each rate
is published on the next working day.)

Importing a day that is already there rewrites it rather than adding a second
one, so the whole history can be written again with every new file.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta, tzinfo

from homeassistant.components.recorder import DATA_INSTANCE
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .rates import Rate

_LOGGER = logging.getLogger(__name__)

# Statistics imported by an integration for one of its own entities say they come from the recorder.
SOURCE = "recorder"


def metadata_for(statistic_id: str, name: str) -> StatisticMetaData:
    return StatisticMetaData(
        source=SOURCE,
        statistic_id=statistic_id,
        name=name,
        # No unit, although the rates are percentages. Home Assistant shows statistics in the
        # unit of the entity's state, and the history sensor's state is a date, which can't
        # have one; from "%" to no unit it would divide every rate by a hundred.
        unit_of_measurement=None,
        unit_class=None,
        mean_type=StatisticMeanType.ARITHMETIC,
        has_sum=False,
    )


def rows_for(rates: list[Rate], time_zone: tzinfo) -> list[StatisticData]:
    """One row per published day, at the start of that day in Home Assistant's time zone.

    Home Assistant groups statistics into days by its own time zone, so a row at
    midnight UTC would fall on the day before anywhere west of UTC. A row has to
    start on a whole hour in UTC, which in a time zone like India's is half past
    midnight. A rate is one number for the whole day, so it is its own mean,
    lowest and highest.
    """
    rows: list[StatisticData] = []
    for rate in rates:
        midnight = datetime.combine(date.fromisoformat(rate.date), datetime.min.time(), tzinfo=time_zone)
        moment = midnight.astimezone(UTC)
        hour = moment.replace(minute=0, second=0, microsecond=0)
        start = hour if hour == moment else hour + timedelta(hours=1)
        rows.append(StatisticData(start=start, mean=rate.rate, min=rate.rate, max=rate.rate))
    return rows


def recording(hass: HomeAssistant) -> bool:
    """Whether there is a recorder to keep statistics in. Without one the rates are still shown."""
    return DATA_INSTANCE in hass.data


def store(hass: HomeAssistant, statistic_id: str, name: str, rates: list[Rate]) -> None:
    """Write the rates into the statistics of the sensor they belong to."""
    if not rates or not recording(hass):
        return
    async_import_statistics(hass, metadata_for(statistic_id, name), rows_for(rates, dt_util.get_default_time_zone()))
    _LOGGER.debug("Wrote %s days of %s into statistics", len(rates), statistic_id)
