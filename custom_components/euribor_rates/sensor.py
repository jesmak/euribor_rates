"""The sensors of one maturity: its newest rate, and the day that rate is from."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_LATEST_DATE, ATTR_LATEST_RATE, ATTR_MATURITY, ATTRIBUTION, DOMAIN
from .coordinator import EuriborConfigEntry, EuriborCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EuriborConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        async_add_entities(
            [EuriborRateSensor(coordinator), EuriborPublishedSensor(coordinator)],
            config_subentry_id=subentry_id,
        )


class EuriborSensor(CoordinatorEntity[EuriborCoordinator], SensorEntity):
    """What both sensors of a maturity share."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.subentry.subentry_id)},
            name=f"Euribor {coordinator.maturity}",
            manufacturer="euribor-rates.eu",
            entry_type=DeviceEntryType.SERVICE,
        )


class EuriborRateSensor(EuriborSensor):
    """The newest published rate, and the history of it in the sensor's statistics."""

    _attr_name = None
    _attr_icon = "mdi:percent-circle-outline"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        # The same unique id as in earlier versions, so the entity keeps its id and history.
        self._attr_unique_id = coordinator.rate_unique_id

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # The first rates were fetched before this entity had an id to store them under.
        self.coordinator.store_pending(self.entity_id)

    @property
    def native_value(self) -> float | None:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        return newest.rate if newest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        return {
            ATTR_LATEST_RATE: newest.rate if newest else None,
            ATTR_LATEST_DATE: newest.date if newest else None,
            ATTR_MATURITY: self.coordinator.maturity,
        }


class EuriborPublishedSensor(EuriborSensor):
    """The day the newest rate was published, which says whether the numbers are still fresh."""

    _attr_translation_key = "published"
    _attr_name = "Published"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.rate_unique_id}_published"

    @property
    def native_value(self) -> datetime | None:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        if newest is None:
            return None
        return datetime.strptime(newest.date, "%Y-%m-%d").replace(tzinfo=UTC)
