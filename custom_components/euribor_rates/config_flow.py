"""Config flow: one Euribor entry, with a maturity, a loan or the ECB's rate added to it at a time."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryData,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    DateSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_DAYS,
    CONF_LOCK_DAYS,
    CONF_MARGIN,
    CONF_MATURITY,
    CONF_NAME,
    CONF_RESET_DATE,
    DEFAULT_DAYS,
    DOMAIN,
    ECB_UNIQUE_ID,
    MATURITIES,
    MAX_DAYS,
    MAX_LOCK_DAYS,
    MIN_DAYS,
    SUBENTRY_ECB,
    SUBENTRY_LOAN,
    SUBENTRY_MATURITY,
    TITLE,
)
from .loans import MONTHS_BY_MATURITY
from .migration import VERSION

DAYS_SELECTOR = NumberSelector(NumberSelectorConfig(min=MIN_DAYS, max=MAX_DAYS, step=1, mode=NumberSelectorMode.BOX))


def maturity_schema(choices: list[str]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_MATURITY): SelectSelector(
                SelectSelectorConfig(options=choices, mode=SelectSelectorMode.DROPDOWN, sort=False)
            ),
            vol.Required(CONF_DAYS, default=DEFAULT_DAYS): DAYS_SELECTOR,
        }
    )


def followed(entry: ConfigEntry) -> set[str]:
    return {subentry.data[CONF_MATURITY] for subentry in entry.subentries.values() if subentry.subentry_type == SUBENTRY_MATURITY}


def subentry_data(maturity: str, days: int) -> ConfigSubentryData:
    return ConfigSubentryData(
        data={CONF_MATURITY: maturity, CONF_DAYS: days},
        subentry_type=SUBENTRY_MATURITY,
        title=maturity,
        unique_id=f"euribor_{maturity}",
    )


class EuriborConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = VERSION
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Adding the integration, together with the first maturity to follow."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=maturity_schema(MATURITIES))

        return self.async_create_entry(
            title=TITLE,
            data={},
            subentries=[subentry_data(user_input[CONF_MATURITY], int(user_input[CONF_DAYS]))],
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_MATURITY: MaturitySubentryFlow, SUBENTRY_LOAN: LoanSubentryFlow, SUBENTRY_ECB: EcbSubentryFlow}


class MaturitySubentryFlow(ConfigSubentryFlow):
    """Following one more maturity, or changing how far back one reaches."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        entry = self._get_entry()
        if user_input is not None:
            data = subentry_data(user_input[CONF_MATURITY], int(user_input[CONF_DAYS]))
            # Home Assistant refuses a unique id that is already there, so a maturity
            # cannot be followed twice even if the list below is somehow bypassed.
            return self.async_create_entry(title=data["title"], data=data["data"], unique_id=data["unique_id"])

        choices = [maturity for maturity in MATURITIES if maturity not in followed(entry)]
        if not choices:
            return self.async_abort(reason="all_configured")

        return self.async_show_form(step_id="user", data_schema=maturity_schema(choices))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """How far back to reach. Saving it fetches that much again and stores it."""
        subentry = self._get_reconfigure_subentry()
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(vol.Schema({vol.Required(CONF_DAYS): DAYS_SELECTOR}), dict(subentry.data)),
                description_placeholders={"maturity": subentry.data[CONF_MATURITY]},
            )

        return self.async_update_and_abort(
            self._get_entry(),
            subentry,
            data={**subentry.data, CONF_DAYS: int(user_input[CONF_DAYS])},
        )


ECB_SCHEMA = vol.Schema({vol.Required(CONF_DAYS, default=DEFAULT_DAYS): DAYS_SELECTOR})


class EcbSubentryFlow(ConfigSubentryFlow):
    """Following the ECB's deposit facility rate, or changing how far back its history reaches."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        entry = self._get_entry()
        if any(subentry.subentry_type == SUBENTRY_ECB for subentry in entry.subentries.values()):
            return self.async_abort(reason="already_configured")
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=ECB_SCHEMA)
        return self.async_create_entry(title="ECB", data={CONF_DAYS: int(user_input[CONF_DAYS])}, unique_id=ECB_UNIQUE_ID)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure", data_schema=self.add_suggested_values_to_schema(ECB_SCHEMA, dict(subentry.data))
            )
        return self.async_update_and_abort(self._get_entry(), subentry, data={CONF_DAYS: int(user_input[CONF_DAYS])})


LOAN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): TextSelector(),
        vol.Required(CONF_MATURITY, default="12 months"): SelectSelector(
            SelectSelectorConfig(options=list(MONTHS_BY_MATURITY), mode=SelectSelectorMode.DROPDOWN, sort=False)
        ),
        vol.Required(CONF_MARGIN): NumberSelector(
            NumberSelectorConfig(min=0, max=20, step=0.001, mode=NumberSelectorMode.BOX, unit_of_measurement="%")
        ),
        vol.Required(CONF_RESET_DATE): DateSelector(),
        vol.Required(CONF_LOCK_DAYS, default=0): NumberSelector(
            NumberSelectorConfig(min=0, max=MAX_LOCK_DAYS, step=1, mode=NumberSelectorMode.BOX)
        ),
    }
)


def loan_data(user_input: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The loan's title and data from the form."""
    return user_input[CONF_NAME].strip(), {
        CONF_MATURITY: user_input[CONF_MATURITY],
        CONF_MARGIN: float(user_input[CONF_MARGIN]),
        CONF_RESET_DATE: user_input[CONF_RESET_DATE],
        CONF_LOCK_DAYS: int(user_input[CONF_LOCK_DAYS]),
    }


class LoanSubentryFlow(ConfigSubentryFlow):
    """A loan whose rate follows a maturity, or a change to one."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors = {}
        if user_input is not None:
            title, data = loan_data(user_input)
            if title:
                return self.async_create_entry(title=title, data=data)
            errors[CONF_NAME] = "name_missing"

        return self.async_show_form(step_id="user", data_schema=self.add_suggested_values_to_schema(LOAN_SCHEMA, user_input), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors = {}
        if user_input is not None:
            title, data = loan_data(user_input)
            if title:
                return self.async_update_and_abort(self._get_entry(), subentry, title=title, data=data)
            errors[CONF_NAME] = "name_missing"

        suggested = user_input or {CONF_NAME: subentry.title, **subentry.data}
        return self.async_show_form(
            step_id="reconfigure", data_schema=self.add_suggested_values_to_schema(LOAN_SCHEMA, suggested), errors=errors
        )
