"""Adding the integration, following more maturities, and changing how far back one reaches."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import (
    CONF_DAYS,
    CONF_MATURITY,
    DOMAIN,
    MATURITIES,
    SUBENTRY_MATURITY,
)

from .conftest import euribor_entry


async def test_adding_the_integration_follows_the_first_maturity(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MATURITY: "12 months", CONF_DAYS: 365}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Euribor"
    entry = result["result"]
    [subentry] = entry.subentries.values()
    assert subentry.subentry_type == SUBENTRY_MATURITY
    assert subentry.data[CONF_MATURITY] == "12 months"
    assert subentry.data[CONF_DAYS] == 365
    assert subentry.unique_id == "euribor_12 months"
    assert hass.states.get("sensor.euribor_12_months") is not None
    assert hass.states.get("sensor.euribor_12_months_published") is not None


async def test_the_integration_is_added_only_once(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    euribor_entry(hass)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_following_one_more_maturity(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_MATURITY), context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"
    offered = result["data_schema"].schema[CONF_MATURITY].config["options"]
    assert "12 months" not in offered, "the maturity already followed is left out"
    assert set(offered) == set(MATURITIES) - {"12 months"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MATURITY: "3 months", CONF_DAYS: 30}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(entry.subentries) == 2
    assert hass.states.get("sensor.euribor_3_months") is not None


async def test_when_every_maturity_is_already_followed(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass, *((maturity, 30) for maturity in MATURITIES))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_MATURITY), context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "all_configured"


async def test_changing_how_far_back_a_maturity_reaches(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    euribor: AiohttpClientMocker,
) -> None:
    entry = euribor_entry(hass, ("12 months", 30))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    [subentry] = entry.subentries.values()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_MATURITY),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"] == {"maturity": "12 months"}

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {CONF_DAYS: 720})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data[CONF_DAYS] == 720
    assert entry.subentries[subentry.subentry_id].data[CONF_MATURITY] == "12 months"
