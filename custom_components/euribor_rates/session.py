import logging
from datetime import datetime
import calendar
import requests
from requests import ConnectTimeout, RequestException
from .const import API_BASE_URL, USER_AGENT, REFERER, SEC_FETCH_MODE

_LOGGER = logging.getLogger(__name__)


class EuriborException(Exception):
    """Base exception for Euribor"""


class EuriborSession:
    _timeout: int
    _series: int
    _days: int

    def __init__(self, days: int, series: int, timeout=20):
        self._timeout = timeout
        self._series = series
        self._days = days

    def call_api(self) -> list[list[str | float]]:
        try:
            now = datetime.utcnow()
            now = now.replace(now.year, now.month, now.day, 0, 0, 0)
            max_ticks = calendar.timegm(now.utctimetuple()) * 1000
            min_ticks = max_ticks - (self._days * 86400000)

            response = requests.get(
                url=f"{API_BASE_URL}?minticks={min_ticks}&maxticks={max_ticks}&series[0]={self._series}",
                headers={
                    "User-Agent": USER_AGENT,
                    "Sec-Fetch-Mode": SEC_FETCH_MODE,
                    "Referer": REFERER
                },
                timeout=self._timeout,
            )

            if response.status_code != 200:
                raise EuriborException(f"{response.status_code} is not valid")

            else:
                result = response.json() if response else {}
                return result[0]['Data']

        except ConnectTimeout as exception:
            raise EuriborException("Timeout error") from exception

        except RequestException as exception:
            raise EuriborException(f"Communication error {exception}") from exception
