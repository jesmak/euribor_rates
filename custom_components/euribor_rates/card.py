"""The Euribor card, which comes with the integration.

The integration serves it from its own folder and adds it to the dashboards' resources, with its version in the URL, so
a browser fetches it again after an upgrade although the file is cached for a month.
"""

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

URL_BASE = f"/{DOMAIN}"
CARD_PATH = f"{URL_BASE}/euribor-card.js"


async def async_serve_card(hass: HomeAssistant) -> None:
    await hass.http.async_register_static_paths([StaticPathConfig(URL_BASE, str(Path(__file__).parent / "www"))])


async def async_add_card_resource(hass: HomeAssistant) -> None:
    url = f"{CARD_PATH}?v={(await async_get_integration(hass, DOMAIN)).version}"
    resources = hass.data[LOVELACE_DATA].resources
    if isinstance(resources, ResourceStorageCollection):
        # Loads the stored resources, if nothing has yet.
        await resources.async_get_info()
    items = resources.async_items()

    # Earlier versions' resources of the card, and copies, which a hand-edited list can have.
    ours = [item for item in items if _path(item["url"]) == CARD_PATH]
    current = next((item for item in ours if item["url"] == url), None)
    if not isinstance(resources, ResourceStorageCollection):
        if current is not None:
            return
        if ours:
            _LOGGER.warning(
                "Dashboard resources are set in YAML, so the Euribor card can't update itself. Change %s in them to %s",
                ours[0]["url"],
                url,
            )
        else:
            _LOGGER.warning(
                "Dashboard resources are set in YAML, so the Euribor card can't add itself. Add url: %s, type: module to them",
                url,
            )
        return

    if not ours:
        await resources.async_create_item({"res_type": "module", "url": url})
        return
    kept = current or ours[0]
    if kept["url"] != url:
        await resources.async_update_item(kept["id"], {"url": url})
    for item in ours:
        if item is not kept:
            await resources.async_delete_item(item["id"])


async def async_remove_card_resource(hass: HomeAssistant) -> None:
    resources = hass.data[LOVELACE_DATA].resources
    if not isinstance(resources, ResourceStorageCollection):
        # Nothing serves the card once the integration is gone, so a line left behind fails on every dashboard.
        for item in resources.async_items():
            if _path(item["url"]) == CARD_PATH:
                _LOGGER.warning(
                    "Dashboard resources are set in YAML, so the Euribor card can't remove itself. Remove %s from them",
                    item["url"],
                )
        return
    await resources.async_get_info()
    for item in list(resources.async_items()):
        if _path(item["url"]) == CARD_PATH:
            await resources.async_delete_item(item["id"])


def _path(url: str) -> str:
    return url.split("?", 1)[0]
