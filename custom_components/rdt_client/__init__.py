"""RDT-Client integration lifecycle (development; not production validated)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant

from .api import RDTClientAPI
from .coordinator import RDTClientSubscriptionCoordinator
from .monitor_coordinator import RDTClientMonitorCoordinator
from .session import create_rdt_session

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create an authenticated session, refresh data, and load sensors."""
    # RDT-Client runs at an IP address and needs cookies retained after login.
    # This session is not shared: we explicitly close it if setup fails or
    # when the config entry unloads.
    session = create_rdt_session(verify_ssl=entry.data.get(CONF_VERIFY_SSL, True))
    try:
        api = RDTClientAPI(
            session=session,
            base_url=entry.data[CONF_URL],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )
        coordinator = RDTClientSubscriptionCoordinator(hass, api)
        await coordinator.async_config_entry_first_refresh()
        # Monitoring is non-critical: an unavailable queue API must not block
        # the existing subscription sensors or the integration startup.
        monitor = RDTClientMonitorCoordinator(hass, api)
        await monitor.async_refresh()
        coordinator.monitor = monitor
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await session.close()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload sensors before closing this entry's HTTP session."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: RDTClientSubscriptionCoordinator = entry.runtime_data
        await coordinator.api.session.close()
    return unloaded
