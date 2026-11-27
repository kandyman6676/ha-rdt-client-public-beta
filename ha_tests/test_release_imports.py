"""Real installed Home Assistant import and minimal sensor contract smoke test."""
from custom_components.rdt_client import async_setup_entry, async_unload_entry
from custom_components.rdt_client.config_flow import RDTClientConfigFlow
from custom_components.rdt_client.monitor_sensor import _MONITOR_FIELDS, RDTClientMonitorSensor
from custom_components.rdt_client.sensor import RDTClientSubscriptionSensor
from custom_components.rdt_client.monitor_coordinator import RDTClientMonitorCoordinator
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.restore_state import RestoreEntity


def test_release_imports_and_minimal_field_set():
    assert callable(async_setup_entry)
    assert callable(async_unload_entry)
    assert RDTClientConfigFlow.VERSION == 1
    assert set(_MONITOR_FIELDS) == {"downloading_count", "download_speed", "last_completed"}
    assert issubclass(RDTClientMonitorSensor, RestoreEntity)
    assert RDTClientSubscriptionSensor is not None
    assert RDTClientMonitorCoordinator is not None
    assert SensorDeviceClass.TIMESTAMP.value == "timestamp"
