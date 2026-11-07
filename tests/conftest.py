"""Shared fixtures: Banco de España's file of rates, shaped like the real one with made-up rates."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import (
    CONF_DAYS,
    CONF_MATURITY,
    CSV_URL,
    DOMAIN,
    SUBENTRY_MATURITY,
)

MATURITY = "12 months"

# A moment for the clock, the day after the newest rate. The history reaches back from it.
NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)

# As the real file has them: the series' codes and descriptions first, another series before Euribor's, a row per
# day from before Euribor began, "_" where a series has no value, and the sources and notes last. The columns are
# €STR, the reference rate, then Euribor's 1 week, 1 month, 3, 6 and 12 months.
ROWS = [
    '"CÓDIGO DE LA SERIE","D_DNBAA572","D_DNBAA172","D_DNBAS172","D_DNBAC172","D_DNBAD172","D_DNBAE172","D_DNBAF172"',
    '"NÚMERO SECUENCIAL","5000001","500002","500003","500004","500005","500006","500007"',
    '"ALIAS DE LA SERIE","TI_1_7.1","TI_1_7.2","TI_1_7.3","TI_1_7.4","TI_1_7.5","TI_1_7.6","TI_1_7.7"',
    '"DESCRIPCIÓN DE LA SERIE","Tipos de interés. ¤STR.","Tipos de interés. Euribor.","1 semana","1 mes","3 meses","6 meses","12 meses"',
    '"DESCRIPCIÓN DE LAS UNIDADES","Porcentaje","Porcentaje","Porcentaje","Porcentaje","Porcentaje","Porcentaje","Porcentaje"',
    '"FRECUENCIA","LABORABLE","DIARIA","DIARIA","DIARIA","DIARIA","DIARIA","DIARIA"',
    '"02 ENE 1979","_","9.000","_","_","_","_","_"',
    '"15 ENE 2025",2.101,"_",2.501,2.601,2.701,2.801,2.901',
    '"12 SEP 2026",2.111,"_",2.511,2.611,2.711,2.811,3.301',
    '"13 SEP 2026",2.112,"_","_",2.612,2.712,2.812,3.318',
    '"14 SEP 2026",2.113,"_",2.513,2.613,2.713,2.813,3.322',
    '"15 SEP 2026",2.114,"_",2.514,2.614,2.714,2.814,3.326',
    '"FUENTE","","EXAMPLE SOURCE","EXAMPLE SOURCE","EXAMPLE SOURCE","EXAMPLE SOURCE","EXAMPLE SOURCE","EXAMPLE SOURCE"',
    '"NOTAS","","TIPO ACT/360","","","","",""',
]
NEWEST_DATE = "2026-09-15"
NEWEST_RATE = 3.326
ETAG = '"5f0e-1"'


def csv_text(rows: list[str] | None = None) -> str:
    return "\r\n".join(ROWS if rows is None else rows) + "\r\n"


def csv_file(rows: list[str] | None = None) -> bytes:
    """The file as Banco de España sends it, in Latin-1."""
    return csv_text(rows).encode("latin-1")


# Note: enabling custom integrations is deliberately not autouse. That fixture builds
# hass, and the recorder fixtures insist on being set up before hass exists, so each
# test asks for them in the order it needs: recorder_mock, then enable_custom_integrations.


@pytest.fixture
def euribor(aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory) -> AiohttpClientMocker:
    """Banco de España, answering with its file. The clock stands at NOW, which the history reaches back from."""
    freezer.move_to(NOW)
    # With no charset, as the real file comes.
    aioclient_mock.get(CSV_URL, content=csv_file(), headers={"Content-Type": "text/csv", "ETag": ETAG})
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
