"""Turning rates into statistics rows."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from homeassistant.components.recorder.models import StatisticMeanType

from custom_components.euribor_rates.rates import Rate
from custom_components.euribor_rates.statistics import metadata_for, rows_for

HELSINKI = ZoneInfo("Europe/Helsinki")


def test_a_row_per_published_day_at_the_start_of_that_day() -> None:
    rows = rows_for([Rate("2026-09-14", 3.312), Rate("2026-09-15", 3.326)], HELSINKI)

    assert len(rows) == 2
    # Midnight in Helsinki, three hours ahead of UTC in September.
    assert rows[0]["start"] == datetime(2026, 9, 13, 21, tzinfo=UTC)
    assert rows[1]["start"] == datetime(2026, 9, 14, 21, tzinfo=UTC)


def test_a_day_west_of_utc_is_not_moved_to_the_day_before() -> None:
    [row] = rows_for([Rate("2026-09-15", 3.326)], ZoneInfo("America/New_York"))
    assert row["start"] == datetime(2026, 9, 15, 4, tzinfo=UTC)


def test_a_day_starting_at_half_past_in_utc_uses_the_first_whole_hour() -> None:
    # India is 5:30 ahead: its 15th starts at 18:30 UTC on the 14th, and 19:00 is 00:30 there.
    [row] = rows_for([Rate("2026-09-15", 3.326)], ZoneInfo("Asia/Kolkata"))
    assert row["start"] == datetime(2026, 9, 14, 19, tzinfo=UTC)


def test_a_rate_is_its_own_mean_lowest_and_highest() -> None:
    [row] = rows_for([Rate("2026-09-15", 3.326)], HELSINKI)
    assert row["mean"] == 3.326
    assert row["min"] == 3.326
    assert row["max"] == 3.326


def test_no_rates_means_no_rows() -> None:
    assert rows_for([], HELSINKI) == []


def test_the_statistics_belong_to_the_sensor_itself() -> None:
    metadata = metadata_for("sensor.euribor_12_months_history", "Euribor 12 months")

    assert metadata["statistic_id"] == "sensor.euribor_12_months_history"
    # Statistics an integration keeps for its own entity say they come from the recorder.
    assert metadata["source"] == "recorder"
    # Without a unit, so they are shown as they are rather than converted to the date's lack of one.
    assert metadata["unit_of_measurement"] is None
    assert metadata["unit_class"] is None
    assert metadata["mean_type"] is StatisticMeanType.ARITHMETIC
    assert metadata["has_sum"] is False
