"""Adding a maturity, and changing how much history it keeps."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import API_URL, CONF_DAYS, CONF_MATURITY, DOMAIN

from .conftest import maturity_entry


async def test_adding_a_maturity(hass: HomeAssistant, euribor: AiohttpClientMocker) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MATURITY: "12 months", CONF_DAYS: 365}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "12 months"
    assert result["data"] == {CONF_MATURITY: "12 months", CONF_DAYS: 365}
    assert result["result"].unique_id == "euribor_12 months", "as earlier versions wrote it"
    assert hass.states.get("sensor.euribor_12_months") is not None


async def test_a_maturity_is_added_only_once(hass: HomeAssistant, euribor: AiohttpClientMocker) -> None:
    maturity_entry(hass)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MATURITY: "12 months", CONF_DAYS: 30}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_the_site_cannot_be_reached(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(API_URL, status=503)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_MATURITY: "1 week", CONF_DAYS: 30})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_changing_how_much_history_is_kept(hass: HomeAssistant, euribor: AiohttpClientMocker) -> None:
    entry = maturity_entry(hass, days=30)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"] == {"maturity": "12 months"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_DAYS: 720})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DAYS] == 720
    assert entry.data[CONF_MATURITY] == "12 months", "the maturity names the entity, so it stays"
