"""Keeping the rates in Home Assistant's long term statistics.

The sensor's state is only ever the newest rate. Everything older lives in the
statistics of that same sensor, which is what a statistics graph card, or
apexcharts with `statistics: { type: mean, period: day }`, reads. Importing a
day that is already there rewrites it rather than adding a second one, so
overlapping requests are safe.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from homeassistant.components.recorder import DATA_INSTANCE, get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant

from .rates import Rate

_LOGGER = logging.getLogger(__name__)

# Statistics imported by an integration for one of its own entities say they come from the recorder.
SOURCE = "recorder"


def metadata_for(statistic_id: str, name: str) -> StatisticMetaData:
    return StatisticMetaData(
        source=SOURCE,
        statistic_id=statistic_id,
        name=name,
        unit_of_measurement=PERCENTAGE,
        # A percentage has no unit to convert to.
        unit_class=None,
        mean_type=StatisticMeanType.ARITHMETIC,
        has_sum=False,
    )


def rows_for(rates: list[Rate]) -> list[StatisticData]:
    """One row per published day, at midnight in UTC.

    A rate is one number for the whole day, so it is its own mean, lowest and highest.
    """
    rows: list[StatisticData] = []
    for rate in rates:
        moment = datetime.strptime(rate.date, "%Y-%m-%d").replace(tzinfo=UTC)
        rows.append(StatisticData(start=moment, mean=rate.rate, min=rate.rate, max=rate.rate))
    return rows


def recording(hass: HomeAssistant) -> bool:
    """Whether there is a recorder to keep statistics in. Without one the rates are still shown."""
    return DATA_INSTANCE in hass.data


def store(hass: HomeAssistant, statistic_id: str, name: str, rates: list[Rate]) -> None:
    """Write the rates into the statistics of the sensor they belong to."""
    if not rates or not recording(hass):
        return
    async_import_statistics(hass, metadata_for(statistic_id, name), rows_for(rates))
    _LOGGER.debug("Wrote %s days of %s into statistics", len(rates), statistic_id)


async def newest_stored(hass: HomeAssistant, statistic_id: str) -> date | None:
    """The day of the newest rate already in statistics, or nothing when there are none."""
    if not recording(hass):
        # Without a recorder nothing is stored, so each request seeds from the start.
        return None

    found = await get_instance(hass).async_add_executor_job(get_last_statistics, hass, 1, statistic_id, True, {"mean"})
    rows = found.get(statistic_id) or []
    if not rows:
        return None

    start = rows[0].get("start")
    if isinstance(start, datetime):
        return start.astimezone(UTC).date()
    if isinstance(start, (int, float)):
        return datetime.fromtimestamp(start, UTC).date()
    return None
