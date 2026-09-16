"""Config flow: a maturity is added by choosing it and how much history to keep."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import EuriborClient
from .const import (
    CONF_DAYS,
    CONF_MATURITY,
    DEFAULT_DAYS,
    DOMAIN,
    MATURITIES,
    MAX_DAYS,
    MIN_DAYS,
    SERIES_BY_MATURITY,
)
from .exceptions import EuriborError

DAYS_SELECTOR = NumberSelector(NumberSelectorConfig(min=MIN_DAYS, max=MAX_DAYS, step=1, mode=NumberSelectorMode.BOX))

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MATURITY): SelectSelector(
            SelectSelectorConfig(options=MATURITIES, mode=SelectSelectorMode.DROPDOWN, sort=False)
        ),
        vol.Required(CONF_DAYS, default=DEFAULT_DAYS): DAYS_SELECTOR,
    }
)

RECONFIGURE_SCHEMA = vol.Schema({vol.Required(CONF_DAYS): DAYS_SELECTOR})


class EuriborConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=USER_SCHEMA)

        maturity = user_input[CONF_MATURITY]
        # The same unique id as earlier versions gave, so a maturity is still added only once.
        await self.async_set_unique_id(f"euribor_{maturity}")
        self._abort_if_unique_id_configured()

        days = int(user_input[CONF_DAYS])
        if not await self._reachable(maturity, days):
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
                errors={"base": "cannot_connect"},
            )

        return self.async_create_entry(title=maturity, data={CONF_MATURITY: maturity, CONF_DAYS: days})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """How much history the sensor keeps. The maturity is what the entity is named after, so it stays."""
        entry = self._get_reconfigure_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(RECONFIGURE_SCHEMA, dict(entry.data)),
                description_placeholders={"maturity": entry.data[CONF_MATURITY]},
            )

        days = int(user_input[CONF_DAYS])
        if not await self._reachable(entry.data[CONF_MATURITY], days):
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(RECONFIGURE_SCHEMA, user_input),
                description_placeholders={"maturity": entry.data[CONF_MATURITY]},
                errors={"base": "cannot_connect"},
            )

        return self.async_update_reload_and_abort(entry, data={**entry.data, CONF_DAYS: days})

    async def _reachable(self, maturity: str, days: int) -> bool:
        try:
            await EuriborClient(self.hass).rates(SERIES_BY_MATURITY[maturity], days)
        except EuriborError:
            return False
        return True
