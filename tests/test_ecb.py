"""The ECB's deposit facility rate: reading its series, its sensors, its statistics and its flow."""

from __future__ import annotations

from datetime import timedelta
from types import MappingProxyType

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_USER, ConfigSubentry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import async_fire_time_changed
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import CONF_DAYS, ECB_UNIQUE_ID, ECB_URL, SUBENTRY_ECB
from custom_components.euribor_rates.ecb import parse_deposit_rates
from custom_components.euribor_rates.exceptions import EuriborError
from custom_components.euribor_rates.rates import Rate

from .conftest import NEWEST_RATE, euribor_entry
from .test_sensors import stored

RATE = "sensor.ecb_deposit_facility_rate"
HISTORY = "sensor.ecb_deposit_facility_rate_history"

HEADER = "KEY,FREQ,REF_AREA,CURRENCY,PROVIDER_FM,INSTRUMENT_FM,PROVIDER_FM_ID,DATA_TYPE_FM,TIME_PERIOD,OBS_VALUE"
# Made-up rates in the series' shape: a value every day, a cut in June 2025, a rise in June 2026 and one in September.
DAYS = [
    ("2025-06-10", "2.25"),
    ("2025-06-11", "2"),
    ("2026-06-16", "2"),
    ("2026-06-17", "2.25"),
    ("2026-09-15", "2.25"),
    ("2026-09-16", "2.5"),
]
LAST_MODIFIED = "Wed, 16 Sep 2026 00:36:12 GMT"


def series(days: list[tuple[str, str]] = DAYS) -> str:
    return "\r\n".join([HEADER, *(f"FM.D.U2.EUR.4F.KR.DFR.LEV,D,U2,EUR,4F,KR,DFR,LEV,{day},{value}" for day, value in days)]) + "\r\n"


@pytest.fixture
def ecb(euribor: AiohttpClientMocker) -> AiohttpClientMocker:
    """The ECB, answering with its series, beside Banco de España."""
    euribor.get(ECB_URL, text=series(), headers={"Content-Type": "text/csv", "Last-Modified": LAST_MODIFIED})
    return euribor


def test_the_newest_rate_took_effect_on_the_first_day_it_had() -> None:
    deposit = parse_deposit_rates(series())
    assert deposit.rates[-1] == Rate("2026-09-16", 2.5)
    assert deposit.effective == "2026-09-16"
    assert parse_deposit_rates(series(DAYS[:5])).effective == "2026-06-17"
    assert parse_deposit_rates(series(DAYS[1:3])).effective == "2025-06-11", "unchanged since the series' first day"


@pytest.mark.parametrize(
    "text",
    [
        "<html>Service unavailable</html>",
        HEADER + "\r\n",
        series([("16 SEP 2026", "2.5")]),
        series([("2026-09-16", "NaN?")]),
    ],
)
def test_something_other_than_the_series_is_an_error(text: str) -> None:
    with pytest.raises(EuriborError):
        parse_deposit_rates(text)


async def test_adding_the_ecb_s_rate_gives_its_sensors_and_history(
    recorder_mock,
    hass: HomeAssistant,
    ecb: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init((entry.entry_id, SUBENTRY_ECB), context={"source": SOURCE_USER})
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {CONF_DAYS: 365})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY

    rate = hass.states.get(RATE)
    assert rate.state == "2.5"
    assert rate.attributes["unit_of_measurement"] == "%"
    assert rate.attributes["effective_date"] == "2026-09-16"
    assert rate.attributes["attribution"] == "Data provided by the European Central Bank"
    assert hass.states.get(HISTORY).state == "2026-09-16"

    rows = await stored(hass, HISTORY)
    assert [row["mean"] for row in rows] == [2.0, 2.25, 2.25, 2.5], "only the days within a year of today"
    assert hass.states.get("sensor.euribor_12_months").state == str(NEWEST_RATE), "the maturity carries on beside it"

    result = await hass.config_entries.subentries.async_init((entry.entry_id, SUBENTRY_ECB), context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_an_unchanged_series_is_not_downloaded_again(
    recorder_mock,
    hass: HomeAssistant,
    ecb: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    entry = euribor_entry(hass)
    hass.config_entries.async_add_subentry(entry, ecb_subentry())
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ecb.clear_requests()
    ecb.get(ECB_URL, status=304)
    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    [call] = [call for call in ecb.mock_calls if str(call[1]) == ECB_URL]
    assert call[3]["If-Modified-Since"] == LAST_MODIFIED
    assert hass.states.get(RATE).state == "2.5"


async def test_the_ecb_down_leaves_the_euribor_sensors_alone(
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    euribor.get(ECB_URL, status=503)
    entry = euribor_entry(hass)
    hass.config_entries.async_add_subentry(entry, ecb_subentry())
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(RATE).state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.euribor_12_months").state == str(NEWEST_RATE)


def ecb_subentry() -> ConfigSubentry:
    return ConfigSubentry(data=MappingProxyType({CONF_DAYS: 365}), subentry_type=SUBENTRY_ECB, title="ECB", unique_id=ECB_UNIQUE_ID)
