import logging
from datetime import (timedelta, datetime)
from typing import Any, Callable, Dict, Optional

from aiohttp import ClientError

from homeassistant import config_entries, core
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .session import EuriborSession
from .const import CONF_DAYS, CONF_MATURITY, DOMAIN, SERIES_WEEK, SERIES_YEAR, SERIES_MONTH, \
    SERIES_HALF_YEAR, SERIES_QUARTER_YEAR

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=3)
ATTRIBUTION = "Data provided by euribor-rates.eu"

ATTR_HISTORY = "history"
ATTR_DATE = "date"
ATTR_RATE = "rate"
ATTR_MATURITY = "maturity"
ATTR_LATEST_DATE = "latest_date"
ATTR_LATEST_RATE = "latest_rate"


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    if config[CONF_MATURITY] == "1 week":
        series = SERIES_WEEK
    elif config[CONF_MATURITY] == "1 month":
        series = SERIES_MONTH
    elif config[CONF_MATURITY] == "3 months":
        series = SERIES_QUARTER_YEAR
    elif config[CONF_MATURITY] == "6 months":
        series = SERIES_HALF_YEAR
    else:
        series = SERIES_YEAR

    session = EuriborSession(config[CONF_DAYS], series)
    await hass.async_add_executor_job(session.call_api)
    async_add_entities(
        [EuriborSensor(
            session,
            config[CONF_MATURITY]
        )],
        update_before_add=True
    )


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    if config[CONF_MATURITY] == "1 week":
        series = SERIES_WEEK
    elif config[CONF_MATURITY] == "1 month":
        series = SERIES_MONTH
    elif config[CONF_MATURITY] == "3 months":
        series = SERIES_QUARTER_YEAR
    elif config[CONF_MATURITY] == "6 months":
        series = SERIES_HALF_YEAR
    else:
        series = SERIES_YEAR

    session = EuriborSession(config[CONF_DAYS], series)
    await hass.async_add_executor_job(session.call_api)
    async_add_entities(
        [EuriborSensor(
            session,
            config[CONF_MATURITY]
        )],
        update_before_add=True
    )


class EuriborSensor(Entity):
    _attr_attribution = ATTRIBUTION
    _attr_icon = "mdi:percent-circle-outline"
    _attr_native_unit_of_measurement = "%"

    def __init__(
            self,
            session: EuriborSession,
            maturity: str
    ):
        super().__init__()
        self._session = session
        self._maturity = maturity
        self._state = None
        self._available = True
        self._attrs = {}

    @property
    def name(self) -> str:
        return f"euribor_{self._maturity.replace(' ', '_')}"

    @property
    def unique_id(self) -> str:
        return f"euribor_{self._maturity.replace(' ', '_')}"

    @property
    def available(self) -> bool:
        return self._available

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self._attrs

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        return "%"

    async def async_update(self):
        try:
            data = await self.hass.async_add_executor_job(self._session.call_api)
            time_format = '%Y-%m-%d'

            latest_date = None
            latest_rate = None
            rates = []

            for entry in data:
                date = datetime.utcfromtimestamp(entry[0] / 1000).strftime(time_format)
                rate = entry[1]

                if latest_date is None or date > latest_date:
                    latest_date = date
                    latest_rate = rate

                rates.append({ATTR_DATE: date, ATTR_RATE: rate})

            self._attrs[ATTR_HISTORY] = rates
            self._attrs[ATTR_LATEST_DATE] = latest_date
            self._attrs[ATTR_LATEST_RATE] = latest_rate
            self._attrs[ATTR_MATURITY] = self._maturity
            self._available = True
            self._state = latest_rate

        except ClientError:
            self._available = False
