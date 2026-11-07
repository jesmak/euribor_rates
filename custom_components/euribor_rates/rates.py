"""Reading Banco de España's file of rates.

The file is a CSV of many interest rate series side by side, a column each, with a row per day since 1979. The series'
codes and descriptions take the first rows, and two rows of sources and notes come last. A day a series has no value
for is "_". The dates are Spanish ("05 NOV 2026").
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass

from .const import SERIES_BY_MATURITY
from .exceptions import EuriborError

MONTHS = {
    "ENE": 1,
    "FEB": 2,
    "MAR": 3,
    "ABR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DIC": 12,
}
DAY = re.compile(r"(\d{2}) ([A-Z]{3}) (\d{4})")
CODES_ROW = "CÓDIGO DE LA SERIE"
MISSING = "_"


@dataclass(frozen=True)
class Rate:
    """One day's rate, its date as YYYY-MM-DD, which is also how the sensor's latest_date attribute shows it."""

    date: str
    rate: float


def parse_rates(text: str) -> dict[str, list[Rate]]:
    """The rates of each Euribor series in the file, by the series' code, oldest first."""
    rows = list(csv.reader(text.splitlines()))
    if not rows or rows[0][:1] != [CODES_ROW]:
        raise EuriborError("Banco de España sent something other than its file of rates")

    columns = {}
    for code in SERIES_BY_MATURITY.values():
        if code not in rows[0]:
            raise EuriborError(f"Banco de España's file has no series {code}")
        columns[code] = rows[0].index(code)
    width = max(columns.values()) + 1

    rates: dict[str, list[Rate]] = {code: [] for code in columns}
    for row in rows[1:]:
        day = DAY.fullmatch(row[0]) if row else None
        if day is None:
            continue
        if day[2] not in MONTHS or len(row) < width:
            raise EuriborError(f"Banco de España's file has a row that can't be read: {row[0]}")
        date = f"{day[3]}-{MONTHS[day[2]]:02d}-{day[1]}"
        for code, column in columns.items():
            if row[column] == MISSING:
                continue
            try:
                rates[code].append(Rate(date, float(row[column])))
            except ValueError as err:
                raise EuriborError(f"Banco de España's file has a rate that can't be read: {row[column]} on {date}") from err

    for code, found in rates.items():
        if not found:
            raise EuriborError(f"Banco de España's file has no rates for {code}")
        found.sort(key=lambda entry: entry.date)
    return rates


def latest(rates: list[Rate]) -> Rate | None:
    """The newest rate, which is the sensor's state."""
    return rates[-1] if rates else None
