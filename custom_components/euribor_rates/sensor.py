"""The sensor of one maturity: the newest rate, with the recent rates in its attributes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATE,
    ATTR_HISTORY,
    ATTR_LATEST_DATE,
    ATTR_LATEST_RATE,
    ATTR_MATURITY,
    ATTR_RATE,
    ATTRIBUTION,
    DOMAIN,
)
from .coordinator import EuriborConfigEntry, EuriborCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EuriborConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EuriborSensor(entry.runtime_data)])


class EuriborSensor(CoordinatorEntity[EuriborCoordinator], SensorEntity):
    """The newest Euribor rate of one maturity."""

    # The history is as long as the days setting and would fill the database; the state is history enough.
    _unrecorded_attributes = frozenset({ATTR_HISTORY})
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:percent-circle-outline"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        maturity = coordinator.maturity
        # The same unique id as in earlier versions, so the entity keeps its id and history.
        self._attr_unique_id = f"euribor_{maturity.replace(' ', '_')}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"Euribor {maturity}",
            manufacturer="euribor-rates.eu",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        return newest.rate if newest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        newest = data.newest if data else None
        return {
            ATTR_HISTORY: [{ATTR_DATE: rate.date, ATTR_RATE: rate.rate} for rate in (data.rates if data else [])],
            ATTR_LATEST_DATE: newest.date if newest else None,
            ATTR_LATEST_RATE: newest.rate if newest else None,
            ATTR_MATURITY: self.coordinator.maturity,
        }
