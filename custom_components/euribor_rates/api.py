"""Banco de España's file of rates, read once for every maturity."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import CSV_URL
from .exceptions import EuriborError
from .rates import Rate, parse_rates

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=60)

# The maturities' updates come due together, so what one of them read is good for the others for this long.
REUSE = timedelta(minutes=5)


@dataclass(frozen=True)
class RateFile:
    """What the file holds. The version grows each time the file is read with rates that differ from the last."""

    version: int
    rates: dict[str, list[Rate]]


class EuriborClient:
    """Reads the file for every maturity at once.

    The file has every rate since 1998 and is about 1.3 MB. It is asked for with the ETag it last came with, so an
    unchanged file costs a 304. The ETag also changes now and then without new rates, which costs a download but
    keeps the version, so nothing is written again.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._lock = asyncio.Lock()
        self._file: RateFile | None = None
        self._etag: str | None = None
        self._checked: datetime | None = None
        self._error: str | None = None

    async def rates(self) -> RateFile:
        async with self._lock:
            now = dt_util.utcnow()
            if self._checked is None or now - self._checked >= REUSE:
                self._checked = now
                try:
                    await self._fetch()
                    self._error = None
                except EuriborError as err:
                    self._error = str(err)
            if self._error is not None:
                raise EuriborError(self._error)
            assert self._file is not None
            return self._file

    async def _fetch(self) -> None:
        headers = {"If-None-Match": self._etag} if self._etag and self._file else {}
        try:
            async with self._session.get(CSV_URL, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 304:
                    return
                if response.status != 200:
                    raise EuriborError(f"Banco de España answered with status {response.status}")
                body = await response.read()
                etag = response.headers.get("ETag")
        except (aiohttp.ClientError, TimeoutError) as err:
            # A timeout's message is empty, and the coordinator logs only the first failure, so the type is the cause.
            raise EuriborError(f"Banco de España couldn't be reached: {str(err) or type(err).__name__}") from err

        # Its Content-Type names no charset, and the file is Latin-1.
        rates = await self._hass.async_add_executor_job(parse_rates, body.decode("latin-1"))
        self._etag = etag
        if self._file and rates == self._file.rates:
            return
        self._file = RateFile((self._file.version + 1) if self._file else 1, rates)
        _LOGGER.debug("Read Banco de España's file, ETag %s", etag)
