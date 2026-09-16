"""The chart endpoint of euribor-rates.eu."""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import API_URL, HEADERS
from .exceptions import EuriborError
from .rates import Rate, parse_rates

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=30)

DAY_IN_MILLISECONDS = 86400000


class EuriborClient:
    def __init__(self, hass: HomeAssistant) -> None:
        self._session = async_get_clientsession(hass)

    async def rates(self, series: int, days: int) -> list[Rate]:
        """The rates of one maturity over the last days, oldest first."""
        midnight = dt_util.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        newest = int(midnight.timestamp()) * 1000
        oldest = newest - days * DAY_IN_MILLISECONDS
        # The series parameter is written out rather than passed as a parameter, because the
        # site wants the brackets of series[0] unescaped.
        url = f"{API_URL}?minticks={oldest}&maxticks={newest}&series[0]={series}"

        try:
            async with self._session.get(url, headers=HEADERS, timeout=TIMEOUT) as response:
                if response.status != 200:
                    raise EuriborError(f"euribor-rates.eu answered with status {response.status}")
                # The site sends its JSON as text/html.
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EuriborError(f"euribor-rates.eu couldn't be reached: {err}") from err
        except ValueError as err:
            raise EuriborError("euribor-rates.eu sent the rates in an unexpected format") from err

        return parse_rates(payload)
