"""Read-only RDT-Client subscription data coordinator (development).

The integration entry lifecycle will create and own the authenticated API client.
Only explicitly selected subscription fields enter coordinator data.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RDTClientAPI, RDTClientError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL_SECONDS
from .subscription import parse_expiration


class RDTClientSubscriptionCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll subscription metadata without publishing private profile fields."""

    def __init__(self, hass: HomeAssistant, api: RDTClientAPI) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"{DOMAIN}_subscription",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            profile = await self.api.get_provider_profile()
        except RDTClientError as err:
            raise UpdateFailed("Unable to refresh RDT-Client subscription") from err

        premium = profile.get("premium")
        if not isinstance(premium, bool):
            premium = None

        return {
            "premium": premium,
            "expiration": parse_expiration(profile.get("expiration")),
        }
