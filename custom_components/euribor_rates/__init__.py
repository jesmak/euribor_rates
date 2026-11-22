"""Euribor rates: the rate of each maturity being followed, with its history in statistics, and loans tied to them.

One config entry holds every maturity and loan, and the ECB's deposit facility rate. Each maturity is a subentry with
its own sensors and its own place in Home Assistant's long term statistics, and so is the ECB's rate. Each loan is a
subentry with sensors of its own.
"""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import EuriborClient
from .card import async_add_card_resource, async_remove_card_resource, async_serve_card
from .const import DOMAIN, SUBENTRY_ECB, SUBENTRY_LOAN, SUBENTRY_MATURITY
from .coordinator import EcbCoordinator, EuriborConfigEntry, EuriborCoordinator, EuriborRuntimeData, LoanCoordinator
from .migration import VERSION, async_migrate_to_subentries, async_remove_empty_devices
from .websocket import async_register_commands

PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    # Runs before any entry is set up, so an entry per maturity becomes one entry
    # with a maturity inside it before Home Assistant tries to load them.
    await async_migrate_to_subentries(hass)
    await async_serve_card(hass)
    async_register_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EuriborConfigEntry) -> bool:
    # A change saved before the update listener is added below has nothing to reload the entry, so it is looked for
    # then.
    modified = entry.modified_at
    await async_add_card_resource(hass)
    # One file holds every maturity, so they share one client.
    client = EuriborClient(hass)
    coordinators = {
        subentry.subentry_id: EuriborCoordinator(hass, entry, subentry, client)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_MATURITY
    }
    loans = {
        subentry.subentry_id: LoanCoordinator(hass, entry, subentry, client)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_LOAN
    }
    ecb = {
        subentry.subentry_id: EcbCoordinator(hass, entry, subentry)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_ECB
    }
    entry.runtime_data = EuriborRuntimeData(coordinators, loans, ecb)

    # The sensors are added first, so the rates read below have an entity to be stored
    # under. A maturity or loan that cannot be read becomes unavailable and keeps trying;
    # it does not stop the others from being set up.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_remove_empty_devices(hass, entry)
    await asyncio.gather(*(coordinator.async_refresh() for coordinator in [*coordinators.values(), *loans.values(), *ecb.values()]))

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    if entry.modified_at != modified:
        # Scheduled, as a reload waits for this setup to finish.
        hass.config_entries.async_schedule_reload(entry.entry_id)
    return True


async def async_update_listener(hass: HomeAssistant, entry: EuriborConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EuriborConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: EuriborConfigEntry) -> None:
    await async_remove_card_resource(hass)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Entries from before 2.0 are converted in async_setup, which runs first.
    # A newer version than this means Home Assistant was downgraded.
    return entry.version <= VERSION
