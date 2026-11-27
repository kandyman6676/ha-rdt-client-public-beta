"""Isolated Home Assistant runtime contracts; no live HTTP or disk operations."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.rdt_client import async_setup_entry, async_unload_entry
from custom_components.rdt_client.api import RDTClientError
from custom_components.rdt_client.coordinator import RDTClientSubscriptionCoordinator
from custom_components.rdt_client.monitor_coordinator import RDTClientMonitorCoordinator
from custom_components.rdt_client.monitor_sensor import RDTClientMonitorSensor
from custom_components.rdt_client.sensor import async_setup_entry as async_setup_sensors


@pytest.mark.asyncio
async def test_runtime_setup_and_clean_unload_without_network():
    """A single owned session serves the two coordinators and is closed on unload."""
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    entry = SimpleNamespace(
        entry_id="example-entry",
        data={"url": "https://example.invalid", "username": "masked", "password": "test-only"},
        runtime_data=None,
    )
    session = MagicMock()
    session.close = AsyncMock()
    api = MagicMock()
    subscription = MagicMock()
    subscription.api = api  # Mirror the real subscription coordinator's API ownership.
    api.session = session  # Mirror the real API client's owned HTTP session.
    subscription.async_config_entry_first_refresh = AsyncMock()
    monitor = MagicMock()
    monitor.async_refresh = AsyncMock()

    with (
        patch("custom_components.rdt_client.create_rdt_session", return_value=session) as session_factory,
        patch("custom_components.rdt_client.RDTClientAPI", return_value=api) as api_factory,
        patch("custom_components.rdt_client.RDTClientSubscriptionCoordinator", return_value=subscription),
        patch("custom_components.rdt_client.RDTClientMonitorCoordinator", return_value=monitor),
    ):
        assert await async_setup_entry(hass, entry)
        session_factory.assert_called_once_with(verify_ssl=True)
        api_factory.assert_called_once()
        subscription.async_config_entry_first_refresh.assert_awaited_once()
        monitor.async_refresh.assert_awaited_once()
        assert subscription.monitor is monitor
        assert entry.runtime_data is subscription
        assert session.close.await_count == 0
        assert await async_unload_entry(hass, entry)
        session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_failure_closes_session_before_loading_sensors():
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = SimpleNamespace(data={"url": "https://example.invalid", "username": "x", "password": "y"})
    session = MagicMock()
    session.close = AsyncMock()
    subscription = MagicMock()
    subscription.async_config_entry_first_refresh = AsyncMock(side_effect=RDTClientError("offline"))
    with (
        patch("custom_components.rdt_client.create_rdt_session", return_value=session),
        patch("custom_components.rdt_client.RDTClientAPI", return_value=MagicMock()),
        patch("custom_components.rdt_client.RDTClientSubscriptionCoordinator", return_value=subscription),
    ):
        with pytest.raises(RDTClientError):
            await async_setup_entry(hass, entry)
    session.close.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_not_awaited()


@pytest.mark.asyncio
async def test_subscription_only_publishes_expiration_and_status(hass):
    payload = {"premium": True, "expiration": "2026-12-25T12:00:00+00:00",
               "userName": "SECRET-ACCOUNT", "token": "SECRET-TOKEN"}
    api = MagicMock(get_provider_profile=AsyncMock(return_value=payload))
    coordinator = RDTClientSubscriptionCoordinator(hass, api)
    result = await coordinator._async_update_data()
    assert result == {"premium": True, "expiration": datetime(2026, 12, 25, 12, tzinfo=timezone.utc)}
    assert "SECRET" not in repr(result)
    api.get_provider_profile.return_value = {"premium": "yes", "expiration": "invalid", "userName": "SECRET"}
    assert await coordinator._async_update_data() == {"premium": None, "expiration": None}
    api.get_provider_profile.side_effect = RDTClientError("SECRET")
    with pytest.raises(UpdateFailed, match="Unable to refresh RDT-Client subscription"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_monitor_retains_latest_reported_completion_and_never_raw_metadata(hass):
    first = int(datetime.now(timezone.utc).timestamp()) - 120
    second = first + 50
    api = MagicMock(
        get_transfer_info=AsyncMock(return_value={"dl_info_speed": 1234, "up_info_speed": 5678}),
        get_torrents=AsyncMock(side_effect=[
            [{"state": "downloading", "completion_on": first,
              "name": "SECRET-NAME", "hash": "SECRET-HASH", "save_path": "/private"}],
            [{"state": "stalledDL", "completion_on": second, "name": "SECRET-NAME"}],
            [],
            [{"state": "uploading", "completion_on": second + 99999, "name": "SECRET-NAME"}],
        ]),
    )
    coordinator = RDTClientMonitorCoordinator(hass, api)
    values = [await coordinator._async_update_data() for _ in range(4)]
    assert set(values[0]) == {"download_speed", "downloading_count", "last_completed"}
    assert values[0]["downloading_count"] == 1
    assert values[0]["download_speed"] == 1234
    assert values[0]["last_completed"] == datetime.fromtimestamp(first, tz=timezone.utc)
    assert values[1]["last_completed"] == datetime.fromtimestamp(second, tz=timezone.utc)
    assert values[2]["downloading_count"] == 0
    assert values[2]["last_completed"] == values[1]["last_completed"]
    assert values[3]["last_completed"] == values[1]["last_completed"]
    assert "SECRET" not in repr(values)
    assert "/private" not in repr(values)


@pytest.mark.asyncio
async def test_monitor_failure_is_sanitized(hass):
    api = MagicMock(
        get_transfer_info=AsyncMock(side_effect=RDTClientError("PRIVATE-NAME")),
        get_torrents=AsyncMock(),
    )
    coordinator = RDTClientMonitorCoordinator(hass, api)
    with pytest.raises(UpdateFailed, match="Unable to refresh RDT-Client download activity") as failure:
        await coordinator._async_update_data()
    assert "PRIVATE" not in str(failure.value)


@pytest.mark.asyncio
async def test_six_sensors_created_and_unique_ids_preserved(hass):
    sub = RDTClientSubscriptionCoordinator(hass, MagicMock())
    sub.async_set_updated_data({"premium": True, "expiration": datetime(2026, 12, 25, tzinfo=timezone.utc)})
    monitor = RDTClientMonitorCoordinator(hass, MagicMock())
    monitor.async_set_updated_data({"download_speed": 5, "downloading_count": 2, "last_completed": None})
    sub.monitor = monitor
    entry = SimpleNamespace(entry_id="example-entry", runtime_data=sub)
    added = Mock()
    await async_setup_sensors(hass, entry, added)
    sensors = added.call_args.args[0]
    assert len(sensors) == 6
    assert {sensor.unique_id for sensor in sensors} == {
        "example-entry_subscription_premium",
        "example-entry_subscription_expiration",
        "example-entry_subscription_days_remaining",
        "example-entry_monitor_download_speed",
        "example-entry_monitor_downloading_count",
        "example-entry_monitor_last_completed",
    }
    values = {sensor.unique_id: sensor.native_value for sensor in sensors}
    assert values["example-entry_subscription_premium"] == "Active"
    assert values["example-entry_monitor_downloading_count"] == 2
    assert all("SECRET" not in str(sensor.extra_state_attributes) for sensor in sensors)


@pytest.mark.asyncio
async def test_timestamp_restore_prefers_newest_and_ignores_bad_state(hass):
    coordinator = RDTClientMonitorCoordinator(hass, MagicMock())
    sensor = RDTClientMonitorSensor(coordinator, "example-entry", "last_completed")
    sensor.async_get_last_state = AsyncMock(
        return_value=SimpleNamespace(state="2026-11-24T12:00:00+00:00")
    )
    with patch(
        "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_added_to_hass",
        new_callable=AsyncMock,
    ):
        await sensor.async_added_to_hass()
    restored = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert sensor.native_value == restored
    coordinator.async_set_updated_data({"last_completed": datetime(2026, 11, 23, tzinfo=timezone.utc)})
    assert sensor.native_value == restored
    newer = datetime(2026, 11, 25, tzinfo=timezone.utc)
    coordinator.async_set_updated_data({"last_completed": newer})
    assert sensor.native_value == newer

    invalid = RDTClientMonitorSensor(coordinator, "example-entry", "last_completed")
    invalid.async_get_last_state = AsyncMock(return_value=SimpleNamespace(state="unknown"))
    with patch(
        "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_added_to_hass",
        new_callable=AsyncMock,
    ):
        await invalid.async_added_to_hass()
    assert invalid._restored_last_completed is None
    assert invalid.native_value == newer
