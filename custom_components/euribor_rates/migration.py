"""From one config entry per maturity to one entry with a maturity inside it.

Each old entry becomes a subentry, and its sensors move with it. Entity IDs and
unique IDs do not change, so history, statistics, dashboards and the names you
have given the entities stay as they are.
"""

from __future__ import annotations

import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_DAYS, CONF_MATURITY, DEFAULT_DAYS, DOMAIN, SUBENTRY_MATURITY, TITLE

_LOGGER = logging.getLogger(__name__)

VERSION = 2


async def async_migrate_to_subentries(hass: HomeAssistant) -> None:
    # The enabled entries come first, so the entry that is kept is an enabled one.
    entries = sorted(hass.config_entries.async_entries(DOMAIN), key=lambda entry: entry.disabled_by is not None)

    def converted(entry: ConfigEntry) -> bool:
        """An entry is done when its maturity lives in a subentry rather than in its own data."""
        return (
            any(subentry.subentry_type == SUBENTRY_MATURITY for subentry in entry.subentries.values())
            and CONF_MATURITY not in entry.data
        )

    old_entries = [entry for entry in entries if not converted(entry)]

    if not old_entries:
        return

    parent = next((entry for entry in entries if converted(entry)), old_entries[0])
    all_disabled = all(entry.disabled_by is not None for entry in entries)
    _LOGGER.info("Moving %s Euribor config entries into subentries of %s", len(old_entries), parent.title)

    registry = er.async_get(hass)
    devices = dr.async_get(hass)

    for entry in old_entries:
        subentry = subentry_for(entry)
        existing = next((item for item in parent.subentries.values() if item.unique_id == subentry.unique_id), None)

        if existing is not None:
            # A migration cut short left this entry behind after its subentry was made.
            subentry = existing
        else:
            hass.config_entries.async_add_subentry(parent, subentry)

        for registered in er.async_entries_for_config_entry(registry, entry.entry_id):
            disabled_by = registered.disabled_by
            if disabled_by is er.RegistryEntryDisabler.CONFIG_ENTRY and not all_disabled:
                # Moving to an enabled entry would clear this flag; keep the entity disabled.
                disabled_by = er.RegistryEntryDisabler.USER
            # The unique id stays as it was, so the entity keeps its id, its history and its statistics.
            registry.async_update_entity(
                registered.entity_id,
                config_entry_id=parent.entry_id,
                config_subentry_id=subentry.subentry_id,
                device_id=None,
                disabled_by=disabled_by,
            )

        # The entry's own device; the maturity is given one of its own when its sensors are added again.
        device = devices.async_get_device_by_identifier((DOMAIN, entry.entry_id), entry.entry_id)
        if device is not None:
            devices.async_remove_device(device.id)

        if entry.entry_id != parent.entry_id:
            await hass.config_entries.async_remove(entry.entry_id)

    _attach_loose_entities(hass, parent)

    if CONF_MATURITY in parent.data or parent.version < VERSION:
        # Last, because until now the parent's data was still that of its own maturity.
        hass.config_entries.async_update_entry(
            parent,
            title=TITLE,
            data={},
            unique_id=None,
            version=VERSION,
        )


def subentry_for(entry: ConfigEntry) -> ConfigSubentry:
    maturity = entry.data[CONF_MATURITY]
    days = int(entry.options.get(CONF_DAYS) or entry.data.get(CONF_DAYS) or DEFAULT_DAYS)
    return ConfigSubentry(
        data=MappingProxyType({CONF_MATURITY: maturity, CONF_DAYS: days}),
        subentry_type=SUBENTRY_MATURITY,
        title=maturity,
        # The same unique id the entry had, so a maturity is still only added once.
        unique_id=f"euribor_{maturity}",
    )


def _attach_loose_entities(hass: HomeAssistant, parent: ConfigEntry) -> None:
    """Put entities left without a subentry back with the maturity they belong to.

    A conversion that ran before this was fixed left the entity on the entry itself,
    which also left it on the entry's old device.
    """
    registry = er.async_get(hass)
    by_unique_id = {
        f"euribor_{subentry.data[CONF_MATURITY].replace(' ', '_')}": subentry
        for subentry in parent.subentries.values()
        if subentry.subentry_type == SUBENTRY_MATURITY
    }

    for registered in er.async_entries_for_config_entry(registry, parent.entry_id):
        if registered.config_subentry_id is not None:
            continue
        # The published sensor carries the rate sensor's unique id with a suffix.
        unique_id = registered.unique_id.removesuffix("_published")
        subentry = by_unique_id.get(unique_id)
        if subentry is None:
            continue
        _LOGGER.info("Attaching %s to the maturity it belongs to", registered.entity_id)
        registry.async_update_entity(
            registered.entity_id,
            config_subentry_id=subentry.subentry_id,
            device_id=None,
        )


def async_remove_empty_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove devices left with no entities.

    The entry used to have one device of its own; each maturity has its own now. This runs
    after the sensors have been added, when a device left over is genuinely unreferenced.
    """
    devices = dr.async_get(hass)
    registry = er.async_get(hass)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        if er.async_entries_for_device(registry, device.id, include_disabled_entities=True):
            continue
        _LOGGER.info("Removing %s, which has no entities left", device.name)
        devices.async_remove_device(device.id)
