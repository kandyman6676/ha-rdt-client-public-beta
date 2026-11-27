"""Minimal public monitor sensors; no names, hashes, paths, or disk data."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .monitor_coordinator import RDTClientMonitorCoordinator
from .subscription import parse_expiration

_MONITOR_FIELDS = {
    "download_speed": ("Download speed", "B/s"),
    "downloading_count": ("Downloading count", None),
    "last_completed": ("Last download completed", None),
}


class RDTClientMonitorSensor(
    CoordinatorEntity[RDTClientMonitorCoordinator], RestoreEntity, SensorEntity
):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: RDTClientMonitorCoordinator, entry_id: str, key: str) -> None:
        if key not in _MONITOR_FIELDS:
            raise ValueError("Unknown monitoring sensor")
        super().__init__(coordinator)
        self._key = key
        self._restored_last_completed: datetime | None = None
        self._attr_unique_id = f"{entry_id}_monitor_{key}"
        self._attr_name, self._attr_native_unit_of_measurement = _MONITOR_FIELDS[key]
        if key == "last_completed":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="RDT-Client",
            manufacturer="RDT-Client",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._key == "last_completed":
            state = await self.async_get_last_state()
            if state is not None:
                self._restored_last_completed = parse_expiration(state.state)

    @property
    def native_value(self) -> int | datetime | None:
        current = (self.coordinator.data or {}).get(self._key)
        if self._key != "last_completed":
            return current
        previous = self._restored_last_completed
        if isinstance(current, datetime):
            if previous is None or current > previous:
                return current
        return previous


def create_monitor_sensors(
    coordinator: RDTClientMonitorCoordinator, entry_id: str
) -> list[RDTClientMonitorSensor]:
    return [RDTClientMonitorSensor(coordinator, entry_id, key) for key in _MONITOR_FIELDS]
