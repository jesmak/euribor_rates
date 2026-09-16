"""Turning rates into statistics rows."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.recorder.models import StatisticMeanType

from custom_components.euribor_rates.rates import Rate
from custom_components.euribor_rates.statistics import metadata_for, rows_for


def test_a_row_per_published_day_at_midnight() -> None:
    rows = rows_for([Rate("2026-09-14", 3.312), Rate("2026-09-15", 3.326)])

    assert len(rows) == 2
    assert rows[0]["start"] == datetime(2026, 9, 14, tzinfo=UTC)
    assert rows[1]["start"] == datetime(2026, 9, 15, tzinfo=UTC)


def test_a_rate_is_its_own_mean_lowest_and_highest() -> None:
    [row] = rows_for([Rate("2026-09-15", 3.326)])
    assert row["mean"] == 3.326
    assert row["min"] == 3.326
    assert row["max"] == 3.326


def test_no_rates_means_no_rows() -> None:
    assert rows_for([]) == []


def test_the_statistics_belong_to_the_sensor_itself() -> None:
    metadata = metadata_for("sensor.euribor_12_months", "Euribor 12 months")

    assert metadata["statistic_id"] == "sensor.euribor_12_months"
    # Statistics an integration keeps for its own entity say they come from the recorder.
    assert metadata["source"] == "recorder"
    assert metadata["unit_of_measurement"] == "%"
    assert metadata["mean_type"] is StatisticMeanType.ARITHMETIC
    assert metadata["has_sum"] is False
    # A percentage has no unit to convert to.
    assert metadata["unit_class"] is None
