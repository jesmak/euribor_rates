"""The sensors of a maturity, and what gets written into statistics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    statistics_during_period,
    validate_statistics,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.components.recorder.common import do_adhoc_statistics
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import API_URL
from custom_components.euribor_rates.statistics import metadata_for

from .conftest import NEWEST_DATE, NEWEST_RATE, euribor_entry

# A moment to pin the clock to, so scheduled refreshes can be made to come due.
NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)

RATE = "sensor.euribor_12_months"
PUBLISHED = "sensor.euribor_12_months_published"
HISTORY = "sensor.euribor_12_months_history"


async def stored(hass: HomeAssistant, statistic_id: str) -> list[dict]:
    """The hourly statistics kept for a sensor."""
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

    history = hass.states.get(HISTORY)
    assert history.state == NEWEST_DATE
    assert history.attributes["device_class"] == "date"
    assert "state_class" not in history.attributes, "the recorder must keep no statistics of its own for it"

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

    rows = await stored(hass, HISTORY)
    assert len(rows) == 4, "one row per published day"
    assert rows[-1]["mean"] == NEWEST_RATE

    # Each at the start of its day in Home Assistant's time zone, which the tests set to US/Pacific.
    written = [datetime.fromtimestamp(row["start"], UTC).isoformat() for row in rows]
    assert written == [
        "2026-09-12T07:00:00+00:00",
        "2026-09-13T07:00:00+00:00",
        "2026-09-14T07:00:00+00:00",
        "2026-09-15T07:00:00+00:00",
    ]
    assert await stored(hass, RATE) == [], "nothing is written into the rate sensor's statistics"


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
    before = len(await stored(hass, HISTORY))

    requests = len(euribor.mock_calls)
    for coordinator in entry.runtime_data.coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(euribor.mock_calls) > requests, "the rates have to have been read a second time"
    assert len(await stored(hass, HISTORY)) == before, "the same days are rewritten, not added again"


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
    assert hass.states.get(HISTORY).state == STATE_UNAVAILABLE


async def test_the_whole_history_is_read_once_and_then_only_the_gap(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    """Only what the integration writes is in the history sensor's statistics, so they
    tell by themselves whether the history has been read."""
    entry = euribor_entry(hass, ("12 months", 365))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

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

    rows = await stored(hass, HISTORY)
    assert len(rows) >= 4, "the days that were read are in statistics"


async def test_the_recorder_keeps_nothing_of_its_own_for_the_history_and_raises_no_issue(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Hours go by and the recorder compiles them, as it does every five minutes."""
    freezer.move_to(NOW)
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await async_wait_recording_done(hass)

    start = NOW
    while start < NOW + timedelta(hours=2):
        freezer.move_to(start + timedelta(minutes=5, seconds=10))
        do_adhoc_statistics(hass, start=start)
        await async_wait_recording_done(hass)
        start += timedelta(minutes=5)

    assert len(await stored(hass, RATE)) == 2, "the recorder did compile the rate sensor's two hours"
    assert len(await stored(hass, HISTORY)) == 4, "and nothing but the four rates is in the history"

    # Neither the repairs nor the statistics check in Developer Tools have anything to say about it.
    assert not [issue for issue in ir.async_get(hass).issues.values() if issue.domain == "sensor"]
    problems = await get_instance(hass).async_add_executor_job(validate_statistics, hass)
    assert HISTORY not in problems
    assert RATE not in problems


async def test_statistics_from_2_0_stay_with_the_rate_sensor_and_the_history_is_read_anew(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    freezer.move_to(NOW)
    entry = euribor_entry(hass, ("12 months", 365))
    [subentry] = entry.subentries.values()
    # What 2.0 left behind: a flag saying the history was read, and the rates in the rate sensor's statistics.
    hass.config_entries.async_update_subentry(entry, subentry, data={**subentry.data, "seeded": True})
    old = [{"start": datetime(2026, 9, 1, tzinfo=UTC), "mean": 3.0, "min": 3.0, "max": 3.0}]
    async_import_statistics(hass, {**metadata_for(RATE, "Euribor 12 months"), "unit_of_measurement": "%"}, old)
    await async_wait_recording_done(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    _method, url, _data, _headers = euribor.mock_calls[0]
    span = int(url.query["maxticks"]) - int(url.query["minticks"])
    assert span >= 365 * 86400000, "the history sensor starts out with the whole year"
    assert len(await stored(hass, HISTORY)) == 4
    assert [row["mean"] for row in await stored(hass, RATE)] == [3.0], "the old statistics are left as they were"


async def test_the_names_and_new_entity_ids_follow_home_assistants_language(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    hass.config.language = "fi"
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Home Assistant builds new entity IDs in its own language for Finnish; existing ones keep theirs.
    ids = sorted(state.entity_id for state in hass.states.async_all("sensor"))
    assert ids == [
        "sensor.euribor_12_kuukautta",
        "sensor.euribor_12_kuukautta_historia",
        "sensor.euribor_12_kuukautta_julkaistu",
    ]
    assert hass.states.get("sensor.euribor_12_kuukautta").name == "Euribor 12 kuukautta"
    assert hass.states.get("sensor.euribor_12_kuukautta_julkaistu").name == "Euribor 12 kuukautta Julkaistu"
    assert hass.states.get("sensor.euribor_12_kuukautta_historia").name == "Euribor 12 kuukautta Historia"
