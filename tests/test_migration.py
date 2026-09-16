"""From one config entry per maturity (1.x) to one entry with maturities inside it.

What matters is that nothing built on the sensors breaks: entity IDs, and with
them history, statistics and the names given to the entities, stay as they were.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.euribor_rates.const import CONF_DAYS, CONF_MATURITY, DOMAIN

RATE_SENSOR = "sensor.euribor_12_months"


def old_entry(
    hass: HomeAssistant,
    maturity: str = "12 months",
    days: int = 365,
    *,
    object_id: str = "euribor_12_months",
    name: str | None = None,
    disabled: bool = False,
) -> MockConfigEntry:
    """A 1.x entry: one maturity, with its sensor registered as 1.x left it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        title=maturity,
        data={CONF_MATURITY: maturity, CONF_DAYS: days},
        unique_id=f"euribor_{maturity}",
        disabled_by=ConfigEntryDisabler.USER if disabled else None,
    )
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "sensor",
        DOMAIN,
        f"euribor_{maturity.replace(' ', '_')}",
        config_entry=entry,
        suggested_object_id=object_id,
        original_name=None,
        disabled_by=er.RegistryEntryDisabler.CONFIG_ENTRY if disabled else None,
    )
    if name is not None:
        er.async_get(hass).async_update_entity(f"sensor.{object_id}", name=name)
    return entry


async def start(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()


async def test_the_maturity_moves_into_the_entry_and_keeps_its_sensor(
    enable_custom_integrations, hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    old_entry(hass, name="Euribor 12 kuukautta")

    await start(hass)

    [entry] = hass.config_entries.async_entries(DOMAIN)
    assert entry.version == 2
    assert entry.title == "Euribor"
    assert entry.data == {}
    assert entry.unique_id is None

    [subentry] = entry.subentries.values()
    assert subentry.unique_id == "euribor_12 months", "as the entry itself was named before"
    assert subentry.data[CONF_MATURITY] == "12 months"
    assert subentry.data[CONF_DAYS] == 365

    registered = er.async_get(hass).async_get(RATE_SENSOR)
    assert registered is not None, "the entity id is what dashboards and statistics use"
    assert registered.unique_id == "euribor_12_months"
    assert registered.config_entry_id == entry.entry_id
    assert registered.config_subentry_id == subentry.subentry_id
    assert registered.name == "Euribor 12 kuukautta", "a name given by hand is kept"


async def test_several_maturities_become_several_subentries(
    enable_custom_integrations, hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    old_entry(hass, "12 months", object_id="euribor_12_months")
    old_entry(hass, "3 months", days=30, object_id="euribor_3_months")

    await start(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1, "the entries are merged into one"
    assert {subentry.data[CONF_MATURITY] for subentry in entries[0].subentries.values()} == {
        "12 months",
        "3 months",
    }
    registry = er.async_get(hass)
    assert registry.async_get("sensor.euribor_12_months") is not None
    assert registry.async_get("sensor.euribor_3_months") is not None


async def test_a_maturity_that_was_disabled_stays_disabled(
    enable_custom_integrations, hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    old_entry(hass, "12 months", object_id="euribor_12_months")
    old_entry(hass, "3 months", object_id="euribor_3_months", disabled=True)

    await start(hass)

    registered = er.async_get(hass).async_get("sensor.euribor_3_months")
    assert registered.disabled_by is er.RegistryEntryDisabler.USER


async def test_migrating_a_second_time_changes_nothing(
    enable_custom_integrations, hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    old_entry(hass)
    await start(hass)
    [entry] = hass.config_entries.async_entries(DOMAIN)
    before = {subentry.subentry_id for subentry in entry.subentries.values()}

    from custom_components.euribor_rates.migration import async_migrate_to_subentries

    await async_migrate_to_subentries(hass)
    await hass.async_block_till_done()

    [entry] = hass.config_entries.async_entries(DOMAIN)
    assert {subentry.subentry_id for subentry in entry.subentries.values()} == before


async def test_an_entry_converted_by_an_earlier_broken_run_is_repaired(
    enable_custom_integrations, hass: HomeAssistant, euribor: AiohttpClientMocker
) -> None:
    """A conversion that ran before this was fixed left entities on the entry itself.

    The entry looks converted — version 2, a maturity subentry — but its sensor was never
    attached to that subentry, so it also stayed on the entry's old device.
    """
    from homeassistant.config_entries import ConfigSubentryData
    from homeassistant.helpers import device_registry as dr

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        minor_version=1,
        title="Euribor",
        data={},
        subentries_data=[
            ConfigSubentryData(
                data={CONF_MATURITY: "12 months", CONF_DAYS: 365},
                subentry_type="maturity",
                title="12 months",
                unique_id="euribor_12 months",
            )
        ],
    )
    entry.add_to_hass(hass)

    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", DOMAIN, "euribor_12_months", config_entry=entry, suggested_object_id="euribor_12_months"
    )
    devices = dr.async_get(hass)
    devices.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, entry.entry_id)}, name="Euribor 12 months"
    )

    await start(hass)

    [subentry] = entry.subentries.values()
    registered = registry.async_get(RATE_SENSOR)
    assert registered.config_subentry_id == subentry.subentry_id, "the sensor belongs to its maturity"
    assert devices.async_get_device_by_identifier((DOMAIN, entry.entry_id), entry.entry_id) is None, (
        "the entry's old device is gone"
    )
