"""Minimal read-only RDT-Client subscription and download-activity sensors."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RDTClientSubscriptionCoordinator
from .monitor_sensor import create_monitor_sensors
from .subscription import days_until_expiration


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: RDTClientSubscriptionCoordinator = entry.runtime_data
    sensors = [
        RDTClientSubscriptionSensor(coordinator, entry.entry_id, key)
        for key in ("premium", "expiration", "days_remaining")
    ]
    monitor = getattr(coordinator, "monitor", None)
    if monitor is not None:
        sensors.extend(create_monitor_sensors(monitor, entry.entry_id))
    async_add_entities(sensors)


class RDTClientSubscriptionSensor(
    CoordinatorEntity[RDTClientSubscriptionCoordinator], SensorEntity
):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: RDTClientSubscriptionCoordinator, entry_id: str, key: str
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry_id}_subscription_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="RDT-Client",
            manufacturer="RDT-Client",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._attr_name = {
            "premium": "Premium status",
            "expiration": "Premium expiration",
            "days_remaining": "Premium days remaining",
        }[key]
        if key == "expiration":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif key == "days_remaining":
            self._attr_native_unit_of_measurement = "d"

    @property
    def native_value(self) -> str | int | datetime | None:
        data = self.coordinator.data or {}
        if self._key == "premium":
            premium = data.get("premium")
            return None if premium is None else ("Active" if premium else "Inactive")
        expiration = data.get("expiration")
        return expiration if self._key == "expiration" else days_until_expiration(expiration)
