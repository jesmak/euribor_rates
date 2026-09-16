"""Fetching one maturity's rates every three hours."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EuriborClient
from .const import CONF_DAYS, CONF_MATURITY, DEFAULT_DAYS, DOMAIN, SERIES_BY_MATURITY, UPDATE_INTERVAL
from .exceptions import EuriborError
from .rates import Rate, latest

_LOGGER = logging.getLogger(__name__)

type EuriborConfigEntry = ConfigEntry[EuriborCoordinator]


@dataclass(frozen=True)
class RateHistory:
    rates: list[Rate]
    newest: Rate | None


class EuriborCoordinator(DataUpdateCoordinator[RateHistory]):
    config_entry: EuriborConfigEntry

    def __init__(self, hass: HomeAssistant, entry: EuriborConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=UPDATE_INTERVAL,
        )
        self.maturity: str = entry.data[CONF_MATURITY]
        # Versions before 2.0 wrote the number of days into the entry's data through an options flow.
        self.days: int = int(entry.options.get(CONF_DAYS) or entry.data.get(CONF_DAYS) or DEFAULT_DAYS)
        self._client = EuriborClient(hass)

    async def _async_update_data(self) -> RateHistory:
        series = SERIES_BY_MATURITY.get(self.maturity)
        if series is None:
            raise UpdateFailed(f"euribor-rates.eu has no maturity called {self.maturity}")

        try:
            rates = await self._client.rates(series, self.days)
        except EuriborError as err:
            raise UpdateFailed(str(err)) from err

        return RateHistory(rates, latest(rates))
