"""Fetching one maturity's rates, and keeping them in statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

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
from .statistics import store

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

    def __init__(self, hass: HomeAssistant, entry: EuriborConfigEntry, subentry: ConfigSubentry, client: EuriborClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {subentry.title}",
            update_interval=UPDATE_INTERVAL,
        )
        self.subentry = subentry
        self.maturity: str = subentry.data[CONF_MATURITY]
        # How far back the history is written.
        self.seed_days: int = int(subentry.data.get(CONF_DAYS) or DEFAULT_DAYS)
        self.rate_unique_id = f"euribor_{self.maturity.replace(' ', '_')}"
        self.history_unique_id = f"{self.rate_unique_id}_history"
        self._client = client
        # The version of the file whose rates were last written into statistics.
        self._stored_version = 0

    async def _async_update_data(self) -> MaturityRates:
        series = SERIES_BY_MATURITY.get(self.maturity)
        if series is None:
            raise UpdateFailed(f"Banco de España has no maturity called {self.maturity}")

        try:
            file = await self._client.rates()
        except EuriborError as err:
            raise UpdateFailed(str(err)) from err

        rates = file.rates[series]
        if file.version != self._stored_version:
            # The file has every rate, so each new one writes the whole history again. A day the source added or
            # corrected afterwards is put right, and the rows already there are rewritten, not added twice.
            first = (dt_util.now().date() - timedelta(days=self.seed_days)).isoformat()
            store(self.hass, self.statistic_id(), f"Euribor {self.maturity}", [rate for rate in rates if rate.date >= first])
            self._stored_version = file.version
        return MaturityRates(latest(rates))

    def statistic_id(self) -> str:
        """The history sensor's entity id, which is what the rates are kept under.

        The sensors are added before the first refresh (async_setup_entry), so it is always registered by then.
        """
        statistic_id = er.async_get(self.hass).async_get_entity_id("sensor", DOMAIN, self.history_unique_id)
        assert statistic_id is not None
        return statistic_id
