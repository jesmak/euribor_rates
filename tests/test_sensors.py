"""The sensors of a maturity, and what gets written into statistics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import API_URL

from .conftest import NEWEST_DATE, NEWEST_RATE, euribor_entry

# A moment to pin the clock to, so scheduled refreshes can be made to come due.
NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)

RATE = "sensor.euribor_12_months"
PUBLISHED = "sensor.euribor_12_months_published"


async def stored(hass: HomeAssistant, statistic_id: str) -> list[dict]:
    """The daily statistics kept for a sensor."""
    await async_wait_recording_done(hass)
    found = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2000, 1, 1, tzinfo=UTC),
        None,
        {statistic_id},
        "hour",
        None,
        {"mean"},
    )
    return found.get(statistic_id, [])


async def async_wait_recording_done(hass: HomeAssistant) -> None:
    await hass.async_block_till_done()
    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()


async def test_the_sensors_hold_the_newest_rate_and_its_day(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    rate = hass.states.get(RATE)
    assert rate.state == str(NEWEST_RATE)
    assert rate.attributes["latest_date"] == NEWEST_DATE
    assert rate.attributes["maturity"] == "12 months"
    assert rate.attributes["unit_of_measurement"] == "%"
    assert rate.attributes["state_class"] == "measurement"
    assert "history" not in rate.attributes, "the history lives in statistics now"

    published = hass.states.get(PUBLISHED)
    assert published.state == "2026-09-15T00:00:00+00:00"
    assert published.attributes["device_class"] == "timestamp"

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_every_rate_read_is_kept_in_statistics(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    rows = await stored(hass, RATE)
    assert len(rows) == 4, "one row per published day"
    assert rows[-1]["mean"] == NEWEST_RATE

    # The sensor held one state for a couple of seconds, so the recorder cannot have
    # compiled a row for the 12th by itself. These are the days that were imported, each
    # written at midnight UTC.
    written = [datetime.fromtimestamp(row["start"], UTC).isoformat() for row in rows]
    assert written == [
        "2026-09-12T00:00:00+00:00",
        "2026-09-13T00:00:00+00:00",
        "2026-09-14T00:00:00+00:00",
        "2026-09-15T00:00:00+00:00",
    ]


async def test_reading_the_same_days_again_does_not_double_them(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    freezer.move_to(NOW)
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    before = len(await stored(hass, RATE))

    requests = len(euribor.mock_calls)
    for coordinator in entry.runtime_data.coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(euribor.mock_calls) > requests, "the rates have to have been read a second time"
    assert len(await stored(hass, RATE)) == before, "the same days are rewritten, not added again"


async def test_the_sensors_are_unavailable_while_the_site_is_down(
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    freezer.move_to(NOW)
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(RATE).state == str(NEWEST_RATE)

    euribor.clear_requests()
    euribor.get(API_URL, status=503)
    freezer.tick(timedelta(hours=4))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(euribor.mock_calls) > 0, "the scheduled update has to have run"
    assert not next(iter(entry.runtime_data.coordinators.values())).last_update_success
    assert hass.states.get(RATE).state == STATE_UNAVAILABLE
    assert hass.states.get(PUBLISHED).state == STATE_UNAVAILABLE


async def test_the_whole_history_is_read_once_and_then_only_the_gap(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    """The recorder compiles rows from the sensor's own state, so what is stored cannot
    say whether the history has been read. The maturity records that itself."""
    entry = euribor_entry(hass, ("12 months", 365))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    [subentry] = entry.subentries.values()
    assert subentry.data.get("seeded") is True, "the maturity remembers its history was read"

    _method, url, _data, _headers = euribor.mock_calls[0]
    span = int(url.query["maxticks"]) - int(url.query["minticks"])
    assert span >= 365 * 86400000, "the first request asked for the whole year"

    await async_wait_recording_done(hass)

    for coordinator in entry.runtime_data.coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()

    _method, url, _data, _headers = euribor.mock_calls[-1]
    span = int(url.query["maxticks"]) - int(url.query["minticks"])
    assert span < 30 * 86400000, "later requests only cover the gap"


async def test_the_first_rates_are_stored_even_though_the_sensor_did_not_exist_yet(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    """The very first read happens as the platform is being set up; the rates still land."""
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    rows = await stored(hass, RATE)
    assert len(rows) >= 4, "the days that were read are in statistics"
