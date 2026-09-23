"""Fetching one maturity's rates, and keeping them in statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EuriborClient
from .const import (
    CONF_DAYS,
    CONF_MATURITY,
    DEFAULT_DAYS,
    DOMAIN,
    SERIES_BY_MATURITY,
    UPDATE_INTERVAL,
)
from .exceptions import EuriborError
from .rates import Rate, latest
from .statistics import newest_stored, store
from .window import span_days

_LOGGER = logging.getLogger(__name__)


@dataclass
class EuriborRuntimeData:
    # By subentry id.
    coordinators: dict[str, EuriborCoordinator]


type EuriborConfigEntry = ConfigEntry[EuriborRuntimeData]


@dataclass(frozen=True)
class MaturityRates:
    """What the sensors of one maturity show."""

    newest: Rate | None


class EuriborCoordinator(DataUpdateCoordinator[MaturityRates]):
    config_entry: EuriborConfigEntry

    def __init__(self, hass: HomeAssistant, entry: EuriborConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {subentry.title}",
            update_interval=UPDATE_INTERVAL,
        )
        self.subentry = subentry
        self.maturity: str = subentry.data[CONF_MATURITY]
        # How far back to reach when there is nothing stored yet.
        self.seed_days: int = int(subentry.data.get(CONF_DAYS) or DEFAULT_DAYS)
        self.rate_unique_id = f"euribor_{self.maturity.replace(' ', '_')}"
        self.history_unique_id = f"{self.rate_unique_id}_history"
        self._client = EuriborClient(hass)
        # Rates fetched before the sensor existed, waiting for an entity id to be stored under.
        self._pending: list[Rate] = []

    async def _async_update_data(self) -> MaturityRates:
        series = SERIES_BY_MATURITY.get(self.maturity)
        if series is None:
            raise UpdateFailed(f"euribor-rates.eu has no maturity called {self.maturity}")

        statistic_id = self.statistic_id()
        # Only the rates written here are in the history sensor's statistics, so the newest
        # of them decides how far back to reach, and none at all means reading the whole history.
        newest = await newest_stored(self.hass, statistic_id) if statistic_id else None
        days = span_days(newest, dt_util.utcnow().date(), self.seed_days)
        _LOGGER.debug("Asking for %s days of %s (newest stored %s)", days, self.maturity, newest)

        try:
            rates = await self._client.rates(series, days)
        except EuriborError as err:
            raise UpdateFailed(str(err)) from err

        self._keep(rates, statistic_id)
        return MaturityRates(latest(rates))

    def statistic_id(self) -> str | None:
        """The history sensor's entity id, which is what the rates are kept under."""
        return er.async_get(self.hass).async_get_entity_id("sensor", DOMAIN, self.history_unique_id)

    def _keep(self, rates: list[Rate], statistic_id: str | None) -> None:
        if statistic_id is None:
            # The first refresh happens before the sensor is added; it stores these itself.
            self._pending = rates
            return
        store(self.hass, statistic_id, f"Euribor {self.maturity}", rates)

    def store_pending(self, entity_id: str) -> None:
        """Called by the sensor once it has an entity id of its own."""
        if self._pending:
            store(self.hass, entity_id, f"Euribor {self.maturity}", self._pending)
            self._pending = []
