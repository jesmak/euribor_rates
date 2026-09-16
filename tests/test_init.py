"""Setting up a maturity and its sensor."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import API_URL
from custom_components.euribor_rates.sensor import EuriborSensor

from .conftest import NEWEST_DATE, NEWEST_RATE, maturity_entry

ENTITY_ID = "sensor.euribor_12_months"


async def test_the_sensor_holds_the_newest_rate(hass: HomeAssistant, euribor: AiohttpClientMocker) -> None:
    entry = maturity_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.state == str(NEWEST_RATE)
    assert state.attributes["latest_date"] == NEWEST_DATE
    assert state.attributes["latest_rate"] == NEWEST_RATE
    assert state.attributes["maturity"] == "12 months"
    assert state.attributes["unit_of_measurement"] == "%"
    assert state.attributes["state_class"] == "measurement"
    assert state.attributes["history"][0] == {"date": "2026-09-12", "rate": 3.301}
    assert len(state.attributes["history"]) == 4

    assert er.async_get(hass).async_get(ENTITY_ID).unique_id == "euribor_12_months", "as in earlier versions"

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_the_history_is_kept_out_of_the_recorder() -> None:
    assert "history" in EuriborSensor._unrecorded_attributes


async def test_the_days_setting_of_an_older_entry_is_still_read(
    hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    entry = maturity_entry(hass, days=365)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    _method, url, _data, _headers = euribor.mock_calls[0]
    span = int(url.query["maxticks"]) - int(url.query["minticks"])
    assert span == 365 * 86400000
    assert url.query["series[0]"] == "4", "12 months is series 4"


async def test_the_sensor_is_unavailable_while_the_site_is_down(
    hass: HomeAssistant, euribor: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    entry = maturity_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == str(NEWEST_RATE)

    euribor.clear_requests()
    euribor.get(API_URL, status=503)
    freezer.tick(timedelta(hours=4))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE


async def test_the_site_being_down_at_startup_is_retried(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(API_URL, status=503)
    entry = maturity_entry(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
