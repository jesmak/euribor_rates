"""Fetching one maturity's rates, and keeping them in statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EuriborClient
from .const import (
    CONF_DAYS,
    CONF_MARGIN,
    CONF_MATURITY,
    CONF_RESET_DATE,
    DEFAULT_DAYS,
    DOMAIN,
    SERIES_BY_MATURITY,
    UPDATE_INTERVAL,
)
from .exceptions import EuriborError
from .loans import MONTHS_BY_MATURITY, LoanRates, loan_rates
from .rates import Rate, latest
from .statistics import store

_LOGGER = logging.getLogger(__name__)


@dataclass
class EuriborRuntimeData:
    # By subentry id.
    coordinators: dict[str, EuriborCoordinator]
    loans: dict[str, LoanCoordinator]


type EuriborConfigEntry = ConfigEntry[EuriborRuntimeData]


@dataclass(frozen=True)
class MaturityRates:
    """What the sensors of one maturity show."""

    newest: Rate | None
    # When the bank saved the file the rates were first read from.
    modified: datetime | None


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
        return MaturityRates(latest(rates), file.modified)

    def statistic_id(self) -> str:
        """The history sensor's entity id, which is what the rates are kept under.

        The sensors are added before the first refresh (async_setup_entry), so it is always registered by then.
        """
        statistic_id = er.async_get(self.hass).async_get_entity_id("sensor", DOMAIN, self.history_unique_id)
        assert statistic_id is not None
        return statistic_id


class LoanCoordinator(DataUpdateCoordinator[LoanRates]):
    """A loan's rates, read from the same file as the maturities'. Nothing is stored, as the file has every rate."""

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
        self.margin = float(subentry.data[CONF_MARGIN])
        self.reset_day = date.fromisoformat(subentry.data[CONF_RESET_DATE])
        self._client = client

    async def _async_update_data(self) -> LoanRates:
        try:
            file = await self._client.rates()
        except EuriborError as err:
            raise UpdateFailed(str(err)) from err

        rates = file.rates[SERIES_BY_MATURITY[self.maturity]]
        return loan_rates(rates, self.reset_day, MONTHS_BY_MATURITY[self.maturity], dt_util.now().date())
