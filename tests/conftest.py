"""Shared fixtures: the rates euribor-rates.eu sends, shaped like the real ones."""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import API_URL, CONF_DAYS, CONF_MATURITY, DOMAIN

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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Lets Home Assistant load integrations from custom_components/."""


@pytest.fixture
def euribor(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """The site, answering with four days of the 12 month rate."""
    # The site sends its JSON as text/html, which the client has to cope with.
    aioclient_mock.get(API_URL, text=json.dumps(payload()), headers={"Content-Type": "text/html"})
    return aioclient_mock


def maturity_entry(hass: HomeAssistant, maturity: str = MATURITY, days: int = 365) -> MockConfigEntry:
    """An entry as earlier versions left it: the days setting lives in the entry's data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=maturity,
        version=1,
        minor_version=1,
        unique_id=f"euribor_{maturity}",
        data={CONF_MATURITY: maturity, CONF_DAYS: days},
    )
    entry.add_to_hass(hass)
    return entry
