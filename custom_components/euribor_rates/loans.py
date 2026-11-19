"""A loan tied to Euribor: its reset days and the rate each one locks.

A loan's rate is reset once per its maturity, a 12 month loan once a year and a 3 month one four times. Each reset
locks the Euribor of the reset day, or of the last day before it with a rate when the day had none.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from .rates import Rate, latest

# The maturities a loan can follow, with the months between its resets.
MONTHS_BY_MATURITY = {"1 month": 1, "3 months": 3, "6 months": 6, "12 months": 12}


@dataclass(frozen=True)
class LoanRates:
    """What the sensors of one loan show."""

    # The Euribor the loan's rate is locked to, None if the file has no rate on or before the reset.
    reference: Rate | None
    # The reset that locked it.
    reset: date
    # The latest reset's rate isn't out yet, so the reference is still the previous reset's.
    pending: bool
    next_reset: date
    newest: Rate | None


def add_months(day: date, months: int) -> date:
    """The same day of the month, months later or earlier, or that month's last day when it is shorter."""
    years, month = divmod(day.month - 1 + months, 12)
    year = day.year + years
    return date(year, month + 1, min(day.day, calendar.monthrange(year, month + 1)[1]))


def resets_around(reset_day: date, months: int, today: date) -> tuple[date, date, date]:
    """The reset before the latest one, the latest one on or before today, and the next one after today.

    Every reset is counted from the one given, so a loan reset on the 31st returns to the 31st after a shorter month.
    """
    count = ((today.year - reset_day.year) * 12 + today.month - reset_day.month) // months
    if add_months(reset_day, count * months) > today:
        count -= 1
    before, latest_reset, next_reset = (add_months(reset_day, (count + step) * months) for step in (-1, 0, 1))
    return before, latest_reset, next_reset


def locked(rates: list[Rate], reset: date) -> Rate | None:
    """The rate a reset locks, or None while it can't be known yet.

    Each rate is published on the next working day. Euribor has no rates on weekends, so a reset on a Saturday or a
    Sunday locks Friday's rate as soon as that is out. A holiday's reset locks the day before it, which shows only
    once a later day's rate is in.
    """
    last_working_day = reset - timedelta(days=max(0, reset.weekday() - 4))
    if not rates or rates[-1].date < last_working_day.isoformat():
        return None
    day = reset.isoformat()
    return next((rate for rate in reversed(rates) if rate.date <= day), None)


def loan_rates(rates: list[Rate], reset_day: date, months: int, today: date) -> LoanRates:
    before, latest_reset, next_reset = resets_around(reset_day, months, today)
    reference = locked(rates, latest_reset)
    if reference is not None:
        return LoanRates(reference, latest_reset, False, next_reset, latest(rates))
    return LoanRates(locked(rates, before), before, True, next_reset, latest(rates))
