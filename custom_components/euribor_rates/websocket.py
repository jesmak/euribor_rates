"""The websocket command the card asks a loan's lock periods with."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import EuriborConfigEntry, LoanCoordinator


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_loan_periods)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/loan_periods", vol.Required("entity_id"): str})
@websocket_api.async_response
async def websocket_loan_periods(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Every reset since the loan's start whose rate is known, with the Euribor it locked, for any of a loan's sensors."""
    coordinator = loan_coordinator(hass, msg["entity_id"])
    if coordinator is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, f"{msg['entity_id']} is not a loan's sensor")
        return
    periods = [
        {"reset": period.reset.isoformat(), "until": period.until.isoformat(), "rate_date": period.rate.date, "rate": period.rate.rate}
        for period in await coordinator.async_periods()
    ]
    connection.send_result(msg["id"], {"periods": periods})


def loan_coordinator(hass: HomeAssistant, entity_id: str) -> LoanCoordinator | None:
    entry = er.async_get(hass).async_get(entity_id)
    if entry is None or entry.platform != DOMAIN or entry.config_entry_id is None or entry.config_subentry_id is None:
        return None
    config_entry: EuriborConfigEntry | None = hass.config_entries.async_get_entry(entry.config_entry_id)
    if config_entry is None or config_entry.state is not ConfigEntryState.LOADED:
        return None
    return config_entry.runtime_data.loans.get(entry.config_subentry_id)
