"""Reading what the site sends."""

from __future__ import annotations

import pytest

from custom_components.euribor_rates.exceptions import EuriborError
from custom_components.euribor_rates.rates import Rate, latest, parse_rates

from .conftest import NEWEST_DATE, NEWEST_RATE, payload


def test_every_day_becomes_a_dated_rate() -> None:
    rates = parse_rates(payload())
    assert len(rates) == 4
    assert rates[0] == Rate("2026-09-12", 3.301)
    assert rates[-1] == Rate(NEWEST_DATE, NEWEST_RATE)


def test_the_newest_rate_is_the_state() -> None:
    assert latest(parse_rates(payload())) == Rate(NEWEST_DATE, NEWEST_RATE)
    assert latest([]) is None


def test_rates_come_back_oldest_first_whatever_order_they_arrive_in() -> None:
    shuffled = [[1789430400000, 3.326], [1789171200000, 3.301]]
    assert [rate.date for rate in parse_rates(payload(shuffled))] == ["2026-09-12", "2026-09-15"]


def test_points_that_make_no_sense_are_left_out() -> None:
    rates = parse_rates(payload([[1789171200000, 3.301], [1789257600000, None], ["nonsense"], []]))
    assert [rate.date for rate in rates] == ["2026-09-12"]


@pytest.mark.parametrize(
    "broken",
    [[], {}, "", [{"Id": 4}], [{"Id": 4, "Data": "no"}], [{"Id": 4, "Data": []}]],
)
def test_an_answer_that_cannot_be_read(broken: object) -> None:
    with pytest.raises(EuriborError):
        parse_rates(broken)
