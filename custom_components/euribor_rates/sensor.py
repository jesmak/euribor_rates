"""The sensors of one maturity (its newest rate, the day that rate is from, and its history), of the ECB's rate and of one loan."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_EFFECTIVE_DATE,
    ATTR_ENTERED_RESET,
    ATTR_LATEST_DATE,
    ATTR_LATEST_RATE,
    ATTR_LOCK_DAYS,
    ATTR_MARGIN,
    ATTR_MATURITY,
    ATTR_PENDING,
    ATTR_RATE_DATE,
    ATTR_RESET_DATE,
    ATTRIBUTION,
    DOMAIN,
    ECB_ATTRIBUTION,
)
from .coordinator import EcbCoordinator, EuriborConfigEntry, EuriborCoordinator, LoanCoordinator
from .rates import Rate


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EuriborConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        async_add_entities(
            [EuriborRateSensor(coordinator), EuriborPublishedSensor(coordinator), EuriborHistorySensor(coordinator)],
            config_subentry_id=subentry_id,
        )
    for subentry_id, ecb in entry.runtime_data.ecb.items():
        async_add_entities([EcbRateSensor(ecb), EcbHistorySensor(ecb)], config_subentry_id=subentry_id)
    for subentry_id, loan in entry.runtime_data.loans.items():
        async_add_entities(
            [LoanRateSensor(loan), LoanReferenceSensor(loan), LoanRateTodaySensor(loan), LoanChangeSensor(loan), LoanNextResetSensor(loan)],
            config_subentry_id=subentry_id,
        )


class EuriborSensor(CoordinatorEntity[EuriborCoordinator], SensorEntity):
    """What the sensors of a maturity share."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.subentry.subentry_id)},
            # Named in Home Assistant's language, "Euribor 12 months" in English.
            translation_key=f"maturity_{coordinator.maturity.replace(' ', '_')}",
            manufacturer="Banco de España",
            entry_type=DeviceEntryType.SERVICE,
        )


class EuriborRateSensor(EuriborSensor):
    """The newest published rate.

    It keeps its state class, so the recorder's statistics of it follow what it showed.
    The rates by the day they are for are in the history sensor's statistics.
    """

    _attr_name = None
    _attr_icon = "mdi:percent-circle-outline"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        # The same unique id as in earlier versions, so the entity keeps its id and history.
        self._attr_unique_id = coordinator.rate_unique_id

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


class EuriborPublishedSensor(EuriborSensor, RestoreEntity):
    """When the newest rate was published, which says whether the numbers are still fresh.

    It is the file's Last-Modified from the read that brought the rate's day. The bank saves the file again during the
    day with the same rates, so the time is kept until a newer day comes, over a restart too. Where it can't be
    restored, the first read gives the file's latest save, which is the same day but can be hours later.
    """

    _attr_translation_key = "published"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.rate_unique_id}_published"
        self._published: datetime | None = None
        # The day of the rate the time belongs to.
        self._rate_date: str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._published = dt_util.parse_datetime(last.state)
            self._rate_date = last.attributes.get(ATTR_LATEST_DATE)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        if data and data.newest and (data.newest.date != self._rate_date or self._published is None):
            self._rate_date = data.newest.date
            self._published = data.modified
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> datetime | None:
        return self._published

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {ATTR_LATEST_DATE: self._rate_date}


class EuriborHistorySensor(EuriborSensor):
    """The rates of every day read, kept in this sensor's statistics under the day each is for.

    Its state is the day of the newest rate. It has no state class, so the recorder keeps no
    statistics of its own for it, and a state that is not a number means Home Assistant does
    not ask for one either.
    """

    _attr_translation_key = "history"
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: EuriborCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.history_unique_id

    @property
    def native_value(self) -> date | None:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        return date.fromisoformat(newest.date) if newest else None


class EcbSensor(CoordinatorEntity[EcbCoordinator], SensorEntity):
    """What the sensors of the ECB's rate share."""

    _attr_attribution = ECB_ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: EcbCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.subentry.subentry_id)},
            translation_key="ecb_deposit_facility",
            manufacturer="European Central Bank",
            entry_type=DeviceEntryType.SERVICE,
        )


class EcbRateSensor(EcbSensor):
    """The deposit facility rate in effect today, and the day it took effect."""

    _attr_name = None
    _attr_icon = "mdi:bank-outline"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: EcbCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.rate_unique_id

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.rates[-1].rate if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {ATTR_EFFECTIVE_DATE: self.coordinator.data.effective if self.coordinator.data else None}


class EcbHistorySensor(EcbSensor):
    """Every day's rate, kept in this sensor's statistics as a maturity's history is."""

    _attr_translation_key = "history"
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: EcbCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.history_unique_id

    @property
    def native_value(self) -> date | None:
        return date.fromisoformat(self.coordinator.data.rates[-1].date) if self.coordinator.data else None


class LoanSensor(CoordinatorEntity[LoanCoordinator], SensorEntity):
    """What the sensors of a loan share: a device named after the loan."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    key: str

    def __init__(self, coordinator: LoanCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.subentry.subentry_id}_{self.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.subentry.subentry_id)},
            name=coordinator.subentry.title,
            entry_type=DeviceEntryType.SERVICE,
        )


class LoanPercentSensor(LoanSensor):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def with_margin(self, rate: Rate | None) -> float | None:
        # Rounded, so a sum like 2.746 + 0.5 doesn't come out as 3.2460000000000004.
        return round(rate.rate + self.coordinator.margin, 6) if rate else None

    def lock(self) -> dict[str, Any]:
        """Which reset the rate is locked by, and whether a newer reset's rate is still to come."""
        data = self.coordinator.data
        return {
            ATTR_RESET_DATE: data.reset.isoformat() if data else None,
            ATTR_PENDING: data.pending if data else None,
        }


class LoanRateSensor(LoanPercentSensor):
    """The loan's interest rate: the locked Euribor and the margin. It is the loan device's main sensor."""

    key = "rate"
    _attr_name = None
    _attr_icon = "mdi:home-percent-outline"

    @property
    def native_value(self) -> float | None:
        return self.with_margin(self.coordinator.data.reference) if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # The maturity, the lock days and the reset day as entered let a card find the loans of a maturity and count
        # their resets as the integration does, from the day entered, so that a 31st returns after a shorter month.
        return {
            ATTR_MARGIN: self.coordinator.margin,
            ATTR_MATURITY: self.coordinator.maturity,
            ATTR_LOCK_DAYS: self.coordinator.lock_days,
            ATTR_ENTERED_RESET: self.coordinator.reset_day.isoformat(),
            **self.lock(),
        }


class LoanReferenceSensor(LoanPercentSensor):
    """The Euribor the loan's rate is locked to."""

    key = "reference_rate"
    _attr_translation_key = "reference_rate"
    _attr_icon = "mdi:percent-circle-outline"

    @property
    def native_value(self) -> float | None:
        reference = self.coordinator.data.reference if self.coordinator.data else None
        return reference.rate if reference else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        reference = self.coordinator.data.reference if self.coordinator.data else None
        return {ATTR_RATE_DATE: reference.date if reference else None, **self.lock()}


class LoanRateTodaySensor(LoanPercentSensor):
    """What the loan's rate would be if it were reset to the newest Euribor."""

    key = "rate_today"
    _attr_translation_key = "rate_today"
    _attr_icon = "mdi:percent-outline"

    @property
    def native_value(self) -> float | None:
        return self.with_margin(self.coordinator.data.newest) if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        newest = self.coordinator.data.newest if self.coordinator.data else None
        return {ATTR_LATEST_DATE: newest.date if newest else None}


class LoanChangeSensor(LoanPercentSensor):
    """How much the loan's rate would change if it were reset to the newest Euribor, in percentage points."""

    key = "change"
    _attr_translation_key = "change"
    _attr_icon = "mdi:swap-vertical"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if not data or not data.reference or not data.newest:
            return None
        return round(data.newest.rate - data.reference.rate, 6)


class LoanNextResetSensor(LoanSensor):
    """The day the loan's rate is next reset."""

    key = "next_reset"
    _attr_translation_key = "next_reset"
    _attr_icon = "mdi:calendar-refresh"
    _attr_device_class = SensorDeviceClass.DATE

    @property
    def native_value(self) -> date | None:
        return self.coordinator.data.next_reset if self.coordinator.data else None
