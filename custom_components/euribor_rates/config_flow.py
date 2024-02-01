import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from .const import (
    DOMAIN,
    MATURITIES,
    CONF_MATURITY,
    CONF_DAYS, SERIES_WEEK, SERIES_MONTH, SERIES_YEAR, SERIES_QUARTER_YEAR, SERIES_HALF_YEAR
)
from .session import EuriborException, EuriborSession

_LOGGER = logging.getLogger(__name__)

CONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MATURITY): vol.All(cv.string, vol.In(MATURITIES)),
        vol.Required(CONF_DAYS, default=30): cv.positive_int,
    }
)

RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MATURITY): vol.All(cv.string, vol.In(MATURITIES)),
        vol.Required(CONF_DAYS): cv.positive_int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, any]) -> str:
    try:
        if data["maturity"] == "1 week":
            series = SERIES_WEEK
        elif data["maturity"] == "1 month":
            series = SERIES_MONTH
        elif data["maturity"] == "3 months":
            series = SERIES_QUARTER_YEAR
        elif data["maturity"] == "6 months":
            series = SERIES_HALF_YEAR
        else:
            series = SERIES_YEAR
        session = EuriborSession(data["days"], series)
        await hass.async_add_executor_job(session.call_api)

    except EuriborException:
        raise ConnectionProblem

    return data["maturity"]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, any] = None) -> FlowResult:

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=CONFIGURE_SCHEMA)

        await self.async_set_unique_id(f"euribor_{user_input[CONF_MATURITY]}")
        self._abort_if_unique_id_configured()

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except ConnectionProblem:
            errors["base"] = "connection_problem"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info, data=user_input)

        return self.async_show_form(step_id="user", data_schema=CONFIGURE_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, any] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=vol.Schema(
                {
                    vol.Required(CONF_DAYS, default=self._config_entry.data.get(CONF_DAYS)): cv.positive_int
                })
            )

        errors = {}

        try:
            user_input[CONF_MATURITY] = self._config_entry.data[CONF_MATURITY]
            await validate_input(self.hass, user_input)
        except ConnectionProblem:
            errors["base"] = "connection_problem"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self.hass.config_entries.async_update_entry(self._config_entry, data=user_input, options=self._config_entry.options)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=RECONFIGURE_SCHEMA, errors=errors)


class ConnectionProblem(HomeAssistantError):
    """Error to indicate there is an issue with the connection"""
