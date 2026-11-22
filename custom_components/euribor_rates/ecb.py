"""The ECB's deposit facility rate, from the ECB Data Portal.

The series has a value for every calendar day since 1999, weekends included, each the rate in effect that day. A change
shows on the day it took effect, not on the day it was decided.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import ECB_URL
from .exceptions import EuriborError
from .rates import Rate

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=60)
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class DepositRates:
    """Every day's rate, oldest first, and the day the newest one took effect."""

    rates: list[Rate]
    effective: str


def parse_deposit_rates(text: str) -> DepositRates:
    rows = list(csv.reader(text.splitlines()))
    if not rows or "TIME_PERIOD" not in rows[0] or "OBS_VALUE" not in rows[0]:
        raise EuriborError("The ECB sent something other than its series of rates")
    day_column, value_column = rows[0].index("TIME_PERIOD"), rows[0].index("OBS_VALUE")

    rates = []
    for row in rows[1:]:
        if len(row) <= max(day_column, value_column) or not DAY.fullmatch(row[day_column]):
            raise EuriborError(f"The ECB's series has a row that can't be read: {','.join(row)}")
        try:
            rates.append(Rate(row[day_column], float(row[value_column])))
        except ValueError as err:
            raise EuriborError(f"The ECB's series has a rate that can't be read: {row[value_column]} on {row[day_column]}") from err
    if not rates:
        raise EuriborError("The ECB's series has no rates")

    rates.sort(key=lambda rate: rate.date)
    effective = rates[-1].date
    for rate in reversed(rates):
        if rate.rate != rates[-1].rate:
            break
        effective = rate.date
    return DepositRates(rates, effective)


class EcbClient:
    """Reads the whole series when it has changed since the last read, which it does once a day.

    The whole series is about 660 kB, 28 kB as it comes compressed, and it is the only way to know the day the newest
    rate took effect when that is further back than the history kept in statistics.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._modified: str | None = None
        self._rates: DepositRates | None = None

    async def rates(self) -> DepositRates:
        headers = {"If-Modified-Since": self._modified} if self._modified and self._rates else {}
        try:
            async with self._session.get(ECB_URL, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 304 and self._rates:
                    return self._rates
                if response.status != 200:
                    raise EuriborError(f"The ECB answered with status {response.status}")
                body = await response.read()
                modified = response.headers.get("Last-Modified")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EuriborError(f"The ECB couldn't be reached: {str(err) or type(err).__name__}") from err

        self._rates = await self._hass.async_add_executor_job(parse_deposit_rates, body.decode())
        self._modified = modified
        _LOGGER.debug("Read the ECB's deposit facility rate, Last-Modified %s", modified)
        return self._rates
