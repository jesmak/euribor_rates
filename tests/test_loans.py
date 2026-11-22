"""Loans: their reset days, the rate each reset locks, their sensors and their flow."""

from __future__ import annotations

from datetime import date
from types import MappingProxyType

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import (
    CONF_LOCK_DAYS,
    CONF_MARGIN,
    CONF_MATURITY,
    CONF_NAME,
    CONF_RESET_DATE,
    SUBENTRY_LOAN,
)
from custom_components.euribor_rates.loans import add_months, loan_rates, locked, resets_around
from custom_components.euribor_rates.rates import Rate

from .conftest import NEWEST_DATE, euribor_entry

# Made-up rates around a Friday 18 December, a Christmas Friday 25 December and New Year's Day, with no rates on the
# weekends or holidays, as in the real file.
RATES = [
    Rate("2026-12-17", 2.410),
    Rate("2026-12-18", 2.420),
    Rate("2026-12-21", 2.430),
    Rate("2026-12-24", 2.440),
    Rate("2026-12-28", 2.450),
]


@pytest.mark.parametrize(
    ("day", "months", "expected"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),
        (date(2026, 1, 31), 3, date(2026, 4, 30)),
        (date(2026, 8, 27), 12, date(2027, 8, 27)),
        (date(2026, 11, 30), 3, date(2027, 2, 28)),
        (date(2026, 3, 31), -1, date(2026, 2, 28)),
        (date(2026, 1, 15), -1, date(2025, 12, 15)),
    ],
)
def test_months_are_added_on_the_same_day_or_the_month_s_last(day: date, months: int, expected: date) -> None:
    assert add_months(day, months) == expected


def test_a_reset_on_the_31st_returns_to_the_31st_after_a_shorter_month() -> None:
    assert resets_around(date(2026, 1, 31), 1, date(2026, 3, 15)) == (date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31))
    assert resets_around(date(2026, 1, 31), 1, date(2026, 3, 31)) == (date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30))


@pytest.mark.parametrize(
    ("reset_day", "today", "expected"),
    [
        # The reset day itself is the latest reset.
        (date(2026, 8, 27), date(2026, 8, 27), (date(2025, 8, 27), date(2026, 8, 27), date(2027, 8, 27))),
        (date(2026, 8, 27), date(2026, 8, 26), (date(2024, 8, 27), date(2025, 8, 27), date(2026, 8, 27))),
        # A reset day in the future counts back.
        (date(2027, 10, 5), date(2026, 11, 19), (date(2025, 10, 5), date(2026, 10, 5), date(2027, 10, 5))),
    ],
)
def test_the_resets_around_today(reset_day: date, today: date, expected: tuple[date, date, date]) -> None:
    assert resets_around(reset_day, 12, today) == expected


def test_a_3_month_loan_counts_its_resets_from_a_day_years_back() -> None:
    assert resets_around(date(2020, 2, 10), 3, date(2026, 11, 19)) == (date(2026, 8, 10), date(2026, 11, 10), date(2027, 2, 10))


def test_a_reset_locks_the_rate_of_its_day_once_published() -> None:
    assert locked(RATES, date(2026, 12, 18)) == Rate("2026-12-18", 2.420)
    assert locked(RATES[:1], date(2026, 12, 18)) is None, "the day's rate comes out the next working day"


def test_a_weekend_reset_locks_friday_s_rate_as_soon_as_it_is_out() -> None:
    assert locked(RATES[:2], date(2026, 12, 19)) == Rate("2026-12-18", 2.420)
    assert locked(RATES[:2], date(2026, 12, 20)) == Rate("2026-12-18", 2.420)
    assert locked(RATES[:1], date(2026, 12, 20)) is None


def test_a_holiday_reset_locks_the_day_before_once_a_later_day_is_in() -> None:
    assert locked(RATES[:4], date(2026, 12, 25)) is None, "a missing Friday can't be told from one not yet published"
    assert locked(RATES, date(2026, 12, 25)) == Rate("2026-12-24", 2.440)


def test_a_weekend_reset_after_a_friday_holiday_waits_for_monday_s_rate() -> None:
    assert locked(RATES[:4], date(2026, 12, 26)) is None, "Friday the 25th had no rate, which shows only on Monday"
    assert locked(RATES, date(2026, 12, 26)) == Rate("2026-12-24", 2.440)


def test_a_lock_days_before_the_reset_counts_only_days_with_a_rate() -> None:
    assert locked(RATES, date(2026, 12, 22), 2) == Rate("2026-12-18", 2.420), "Monday 21 and Friday 18 are the two days before"
    assert locked(RATES, date(2026, 12, 21), 2) == Rate("2026-12-17", 2.410), "the weekend is skipped"
    assert locked(RATES, date(2026, 12, 28), 1) == Rate("2026-12-24", 2.440), "Christmas Friday had no rate"


def test_a_lock_days_before_the_reset_is_known_once_the_day_before_is_out() -> None:
    assert locked(RATES[:2], date(2026, 12, 21), 1) == Rate("2026-12-18", 2.420), "Friday is the last working day before Monday"
    assert locked(RATES[:1], date(2026, 12, 21), 1) is None
    assert locked(RATES[:2], date(2026, 12, 22), 1) is None, "Monday's rate isn't out yet"


def test_a_lock_before_the_first_rate_locks_nothing() -> None:
    assert locked(RATES, date(2026, 12, 18), 2) is None


def test_a_reset_before_any_rate_locks_nothing() -> None:
    assert locked(RATES, date(1998, 6, 1)) is None
    assert locked([], date(2026, 12, 18)) is None


def test_until_the_reset_s_rate_is_out_the_loan_keeps_the_previous_one() -> None:
    rates = [Rate("2025-12-18", 2.100), *RATES[:1]]

    pending = loan_rates(rates, date(2026, 12, 18), 12, date(2026, 12, 18))

    assert pending.pending
    assert pending.reset == date(2025, 12, 18)
    assert pending.reference == Rate("2025-12-18", 2.100)
    assert pending.next_reset == date(2027, 12, 18)
    assert pending.newest == Rate("2026-12-17", 2.410)

    locked_now = loan_rates([*rates, RATES[1]], date(2026, 12, 18), 12, date(2026, 12, 19))

    assert not locked_now.pending
    assert locked_now.reset == date(2026, 12, 18)
    assert locked_now.reference == Rate("2026-12-18", 2.420)


def loan(reset_date: str = "2026-09-14") -> ConfigSubentry:
    """A 12 month home loan with a margin of 0.5."""
    return ConfigSubentry(
        data=MappingProxyType({CONF_MATURITY: "12 months", CONF_MARGIN: 0.5, CONF_RESET_DATE: reset_date}),
        subentry_type=SUBENTRY_LOAN,
        title="Home loan",
        unique_id=None,
    )


async def test_a_loan_s_sensors(
    recorder_mock,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    hass.config_entries.async_add_subentry(entry, loan())
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    rate = hass.states.get("sensor.home_loan")
    assert rate.state == "3.822", "the 12 months' rate of Monday 14 September and the margin"
    assert rate.attributes["unit_of_measurement"] == "%"
    assert rate.attributes["margin"] == 0.5
    assert rate.attributes["maturity"] == "12 months"
    assert rate.attributes["lock_days"] == 0
    assert rate.attributes["entered_reset"] == "2026-09-14"
    assert rate.attributes["reset_date"] == "2026-09-14"
    assert rate.attributes["pending"] is False

    reference = hass.states.get("sensor.home_loan_reference_rate")
    assert reference.state == "3.322"
    assert reference.attributes["rate_date"] == "2026-09-14"

    today = hass.states.get("sensor.home_loan_rate_at_the_newest_euribor")
    assert today.state == "3.826"
    assert today.attributes["latest_date"] == NEWEST_DATE

    change = hass.states.get("sensor.home_loan_change_at_the_newest_euribor")
    assert change.state == "0.004", "the newest Euribor less the locked one"
    assert change.attributes["unit_of_measurement"] == "%"

    assert hass.states.get("sensor.home_loan_next_reset").state == "2027-09-14"

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert "Home loan" in {device.name for device in devices}, "the loan's device isn't taken for a leftover"


async def test_a_loan_reset_today_shows_the_previous_rate_as_pending(
    recorder_mock,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    hass.config_entries.async_add_subentry(entry, loan(reset_date="2026-09-16"))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    rate = hass.states.get("sensor.home_loan")
    assert rate.state == "3.401", "the rate of the last day on or before the previous reset, 16 September 2025"
    assert rate.attributes["reset_date"] == "2025-09-16"
    assert rate.attributes["pending"] is True
    assert hass.states.get("sensor.home_loan_reference_rate").attributes["rate_date"] == "2025-01-15"


async def test_adding_and_changing_a_loan(
    recorder_mock,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init((entry.entry_id, SUBENTRY_LOAN), context={"source": SOURCE_USER})
    assert result["step_id"] == "user"

    form = {CONF_NAME: "  ", CONF_MATURITY: "3 months", CONF_MARGIN: 0.7, CONF_RESET_DATE: "2026-06-14"}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], form)
    assert result["errors"] == {CONF_NAME: "name_missing"}

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {**form, CONF_NAME: "Cabin loan"})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    [subentry] = [subentry for subentry in entry.subentries.values() if subentry.subentry_type == SUBENTRY_LOAN]
    assert subentry.title == "Cabin loan"
    assert subentry.data == {CONF_MATURITY: "3 months", CONF_MARGIN: 0.7, CONF_RESET_DATE: "2026-06-14", CONF_LOCK_DAYS: 0}
    assert hass.states.get("sensor.cabin_loan").state == "3.413", "the 3 months' rate of 14 September and the margin"
    assert hass.states.get("sensor.cabin_loan_next_reset").state == "2026-12-14"

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_LOAN),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {**form, CONF_NAME: "Cabin loan", CONF_MARGIN: 0.65})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_MARGIN] == 0.65
    assert hass.states.get("sensor.cabin_loan").state == "3.363", "the entry is reloaded with the new margin"

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_LOAN),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**form, CONF_NAME: "Cabin loan", CONF_MARGIN: 0.65, CONF_LOCK_DAYS: 2}
    )
    await hass.async_block_till_done()

    assert entry.subentries[subentry.subentry_id].data[CONF_LOCK_DAYS] == 2
    reference = hass.states.get("sensor.cabin_loan_reference_rate")
    assert reference.attributes["rate_date"] == "2026-09-12", "two days with a rate before Monday 14 September"
    assert reference.state == "2.711"
