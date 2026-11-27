"""Read-only RDT-Client activity coordinator; no storage or file operations."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RDTClientAPI, RDTClientError
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN
from .download_completion import most_recent_completion
from .transfer import summarize_downloads

_LOGGER = logging.getLogger(__name__)


class RDTClientMonitorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll only sanitized download counts/speed and completed timestamps."""

    def __init__(self, hass: HomeAssistant, api: RDTClientAPI) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_monitor",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        self._last_completed: datetime | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            transfer = await self.api.get_transfer_info()
            torrents = await self.api.get_torrents()
            summary = summarize_downloads(transfer, torrents)
            completed = most_recent_completion(torrents)
            if completed is not None and (
                self._last_completed is None or completed > self._last_completed
            ):
                self._last_completed = completed
            return {
                "download_speed": summary["download_speed"],
                "downloading_count": summary["downloading_count"],
                "last_completed": self._last_completed,
            }
        except (RDTClientError, ValueError, TypeError):
            # Never log a raw torrent payload, title, private path, or token.
            raise UpdateFailed("Unable to refresh RDT-Client download activity") from None
