"""Reading Banco de España's file, and fetching it."""

from __future__ import annotations

from datetime import timedelta

import aiohttp
import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.api import EuriborClient
from custom_components.euribor_rates.const import CSV_URL
from custom_components.euribor_rates.exceptions import EuriborError
from custom_components.euribor_rates.rates import Rate, latest, parse_rates

from .conftest import ETAG, NEWEST_DATE, NEWEST_RATE, ROWS, csv_file, csv_text

TWELVE_MONTHS = "D_DNBAF172"
ONE_WEEK = "D_DNBAS172"


def test_every_day_of_a_series_becomes_a_dated_rate() -> None:
    rates = parse_rates(csv_text())[TWELVE_MONTHS]
    assert rates == [
        Rate("2025-01-15", 2.901),
        Rate("2026-09-12", 3.301),
        Rate("2026-09-13", 3.318),
        Rate("2026-09-14", 3.322),
        Rate(NEWEST_DATE, NEWEST_RATE),
    ]


def test_every_maturity_has_its_own_series() -> None:
    rates = parse_rates(csv_text())
    assert [found[-1].rate for found in rates.values()] == [2.514, 2.614, 2.714, 2.814, NEWEST_RATE]


def test_a_day_without_a_value_is_left_out() -> None:
    dates = [rate.date for rate in parse_rates(csv_text())[ONE_WEEK]]
    assert "2026-09-13" not in dates
    assert "1979-01-02" not in dates, "the days before Euribor began have no values"


def test_the_series_are_found_by_their_codes_wherever_they_are() -> None:
    # The 12 months' column swapped with the 1 week's.
    swapped = []
    for row in ROWS:
        cells = row.split(",")
        cells[3], cells[7] = cells[7], cells[3]
        swapped.append(",".join(cells))
    assert parse_rates(csv_text(swapped))[TWELVE_MONTHS] == parse_rates(csv_text())[TWELVE_MONTHS]


def test_the_newest_rate_is_the_state() -> None:
    assert latest(parse_rates(csv_text())[TWELVE_MONTHS]) == Rate(NEWEST_DATE, NEWEST_RATE)
    assert latest([]) is None


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        ("", "something other than its file"),
        ("<html><body>Mantenimiento</body></html>", "something other than its file"),
        (csv_text([ROWS[0].replace("D_DNBAD172", "D_OTHER")] + ROWS[1:]), "no series D_DNBAD172"),
        (
            csv_text(ROWS[:8] + ['"16 SPT 2026",2.1,"_",2.5,2.6,2.7,2.8,3.3'] + ROWS[8:]),
            "row that can't be read: 16 SPT 2026",
        ),
        (csv_text(ROWS[:8] + ['"16 SEP 2026",2.1,"_",2.5'] + ROWS[8:]), "row that can't be read: 16 SEP 2026"),
        (
            csv_text(ROWS[:8] + ['"16 SEP 2026",2.1,"_",2.5,2.6,2.7,2.8,"3,3"'] + ROWS[8:]),
            "rate that can't be read: 3,3 on 2026-09-16",
        ),
        (csv_text(ROWS[:7] + ROWS[12:]), "no rates for D_DNBAS172"),
    ],
)
def test_a_file_that_cannot_be_read(broken: str, message: str) -> None:
    with pytest.raises(EuriborError, match=message):
        parse_rates(broken)


async def test_the_file_is_read_as_latin_1(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    # Its Content-Type names no charset, and the file isn't UTF-8.
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"Content-Type": "text/csv", "ETag": ETAG})
    file = await EuriborClient(hass).rates()
    assert file.rates[TWELVE_MONTHS][-1] == Rate(NEWEST_DATE, NEWEST_RATE)
    assert file.version == 1


async def test_an_unchanged_file_is_asked_for_by_its_etag_and_kept(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"ETag": ETAG})
    client = EuriborClient(hass)
    first = await client.rates()

    aioclient_mock.clear_requests()
    aioclient_mock.get(CSV_URL, status=304)
    freezer.tick(timedelta(hours=1))
    again = await client.rates()

    [(_method, _url, _data, headers)] = aioclient_mock.mock_calls
    assert headers == {"If-None-Match": ETAG}
    assert again == first, "the same file, at the same version"


async def test_a_file_with_changed_rates_gets_a_new_version(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"ETag": ETAG})
    client = EuriborClient(hass)
    assert (await client.rates()).version == 1

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        CSV_URL, content=csv_file(ROWS + ['"16 SEP 2026",2.115,"_",2.515,2.615,2.715,2.815,3.331']), headers={"ETag": '"5f0e-2"'}
    )
    freezer.tick(timedelta(hours=1))
    file = await client.rates()
    assert file.version == 2
    assert file.rates[TWELVE_MONTHS][-1] == Rate("2026-09-16", 3.331)


async def test_a_new_etag_with_the_same_rates_keeps_the_version(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    """The file is saved again now and then with nothing new in it, so nothing needs writing again."""
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"ETag": ETAG})
    client = EuriborClient(hass)
    await client.rates()

    aioclient_mock.clear_requests()
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"ETag": '"5f0e-2"'})
    freezer.tick(timedelta(hours=1))
    assert (await client.rates()).version == 1

    aioclient_mock.clear_requests()
    aioclient_mock.get(CSV_URL, status=304)
    freezer.tick(timedelta(hours=1))
    await client.rates()
    [(_method, _url, _data, headers)] = aioclient_mock.mock_calls
    assert headers == {"If-None-Match": '"5f0e-2"'}, "asked for by the newest ETag"


async def test_the_maturities_updating_together_share_one_request(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"ETag": ETAG})
    client = EuriborClient(hass)
    await client.rates()
    freezer.tick(timedelta(minutes=4))
    await client.rates()
    assert aioclient_mock.call_count == 1

    freezer.tick(timedelta(minutes=2))
    await client.rates()
    assert aioclient_mock.call_count == 2


async def test_a_failure_is_shared_too(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory) -> None:
    aioclient_mock.get(CSV_URL, status=503)
    client = EuriborClient(hass)
    for _ in range(2):
        with pytest.raises(EuriborError, match="status 503"):
            await client.rates()
    assert aioclient_mock.call_count == 1, "the second maturity is told the same, without asking again"


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (TimeoutError(), "Banco de España couldn't be reached: TimeoutError"),
        (
            aiohttp.ClientConnectionError("Connection refused"),
            "Banco de España couldn't be reached: Connection refused",
        ),
    ],
)
async def test_an_error_without_a_message_is_named(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, error, message) -> None:
    aioclient_mock.get(CSV_URL, exc=error)
    with pytest.raises(EuriborError) as raised:
        await EuriborClient(hass).rates()
    assert str(raised.value) == message
