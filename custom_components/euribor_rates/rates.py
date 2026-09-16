"""Reading the rates euribor-rates.eu sends.

The site answers with what its own charts read: one series, holding a point per
published day as a pair of a millisecond timestamp and the rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .exceptions import EuriborError

DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class Rate:
    """One day's rate, the date written the way the sensor's attributes have always had it."""

    date: str
    rate: float


def parse_rates(payload: Any) -> list[Rate]:
    """The rates of a series, oldest first."""
    if not isinstance(payload, list) or not payload:
        raise EuriborError("euribor-rates.eu sent no series")

    series = payload[0]
    if not isinstance(series, dict) or not isinstance(series.get("Data"), list):
        raise EuriborError("euribor-rates.eu sent the rates in an unexpected format")

    rates = []
    for point in series["Data"]:
        if not isinstance(point, list) or len(point) < 2:
            continue
        moment, rate = point[0], point[1]
        if moment is None or rate is None:
            continue
        try:
            date = datetime.fromtimestamp(int(moment) / 1000, UTC).strftime(DATE_FORMAT)
            rates.append(Rate(date, float(rate)))
        except (TypeError, ValueError, OSError, OverflowError):
            continue

    if not rates:
        raise EuriborError("euribor-rates.eu sent no rates")
    return sorted(rates, key=lambda entry: entry.date)


def latest(rates: list[Rate]) -> Rate | None:
    """The newest rate, which is the sensor's state."""
    return rates[-1] if rates else None
