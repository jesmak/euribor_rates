"""Shared fixtures: the rates euribor-rates.eu sends, shaped like the real ones."""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import (
    API_URL,
    CONF_DAYS,
    CONF_MATURITY,
    DOMAIN,
    SUBENTRY_MATURITY,
)

MATURITY = "12 months"
SERIES = 4

# Four working days, as the site sends them: a millisecond timestamp and the rate.
POINTS = [
    [1789171200000, 3.301],
    [1789257600000, 3.318],
    [1789344000000, 3.322],
    [1789430400000, 3.326],
]
NEWEST_DATE = "2026-09-15"
NEWEST_RATE = 3.326


def payload(points: list[list[Any]] | None = None, series: int = SERIES) -> list[dict[str, Any]]:
    return [{"Id": series, "Data": POINTS if points is None else points}]


# Note: enabling custom integrations is deliberately not autouse. That fixture builds
# hass, and the recorder fixtures insist on being set up before hass exists, so each
# test asks for them in the order it needs: recorder_mock, then enable_custom_integrations.


@pytest.fixture
def euribor(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """The site, answering with four days of the 12 month rate."""
    # The site sends its JSON as text/html, which the client has to cope with.
    aioclient_mock.get(API_URL, text=json.dumps(payload()), headers={"Content-Type": "text/html"})
    return aioclient_mock


def euribor_entry(hass: HomeAssistant, *maturities: tuple[str, int]) -> MockConfigEntry:
    """The Euribor entry, with a subentry per maturity it follows."""
    from homeassistant.config_entries import ConfigSubentryData

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Euribor",
        version=2,
        minor_version=1,
        unique_id=DOMAIN,
        data={},
        subentries_data=[
            ConfigSubentryData(
                data={CONF_MATURITY: maturity, CONF_DAYS: days},
                subentry_type=SUBENTRY_MATURITY,
                title=maturity,
                unique_id=f"euribor_{maturity}",
            )
            for maturity, days in (maturities or ((MATURITY, 365),))
        ],
    )
    entry.add_to_hass(hass)
    return entry
