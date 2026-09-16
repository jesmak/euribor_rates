"""How far back each request reaches."""

from __future__ import annotations

from datetime import date

import pytest

from custom_components.euribor_rates.const import MAX_DAYS
from custom_components.euribor_rates.window import span_days

TODAY = date(2026, 9, 16)


def test_nothing_stored_yet_reads_the_whole_history_asked_for() -> None:
    # One day more than asked, so the oldest day cannot fall outside the request.
    assert span_days(None, TODAY, seed=365) == 366


@pytest.mark.parametrize(
    ("newest", "expected"),
    [
        (date(2026, 9, 16), 1),  # already have today: still ask, but only for today
        (date(2026, 9, 15), 2),  # yesterday
        (date(2026, 9, 11), 6),  # a long weekend
        (date(2026, 8, 27), 21),  # a three week outage heals itself
    ],
)
def test_the_window_reaches_back_to_the_newest_rate_stored(newest: date, expected: int) -> None:
    assert span_days(newest, TODAY, seed=365) == expected


def test_a_rate_from_the_future_does_not_ask_for_a_negative_span() -> None:
    assert span_days(date(2026, 9, 20), TODAY, seed=365) == 1


def test_the_window_never_grows_past_what_the_site_will_serve() -> None:
    assert span_days(date(1999, 1, 1), TODAY, seed=365) == MAX_DAYS
    assert span_days(None, TODAY, seed=99999) == MAX_DAYS
