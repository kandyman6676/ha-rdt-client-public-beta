"""Async read-only API client for RDT-Client's qBittorrent-compatible endpoints.

Development module: not a complete Home Assistant integration.
The caller owns the aiohttp ClientSession. For IP-hosted instances, configure
aiohttp.CookieJar(unsafe=True) so session cookies are retained.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

from .const import API_LOGIN, API_PROVIDER_PROFILE, API_TORRENTS_INFO, API_TRANSFER_INFO


class RDTClientError(Exception):
    """RDT-Client could not return usable data."""


class RDTClientAuthenticationError(RDTClientError):
    """Credentials or session were rejected."""


@dataclass
class RDTClientAPI:
    """Read-only API wrapper with one re-login attempt on HTTP 401/403."""

    session: ClientSession
    base_url: str
    username: str = field(repr=False)
    password: str = field(repr=False)
    _logged_in: bool = field(default=False, init=False, repr=False)
    _auth_generation: int = field(default=0, init=False, repr=False)
    _auth_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        # Protect direct API callers as well as callers using the config flow.
        from .config_url import normalize_server_url

        self.base_url = normalize_server_url(self.base_url)

    async def login(self) -> None:
        """Authenticate with form data; HTTP 200 alone is not success."""
        async with self._auth_lock:
            await self._login_unlocked()

    async def _login_unlocked(self) -> None:
        try:
            async with self.session.post(
                f"{self.base_url}{API_LOGIN}",
                data={"username": self.username, "password": self.password},
                allow_redirects=False,
                timeout=ClientTimeout(total=15),
            ) as response:
                if 300 <= response.status < 400:
                    raise RDTClientAuthenticationError("RDT-Client login redirect refused")
                response.raise_for_status()
                accepted = (await response.text()).strip() == "Ok."
        except (ClientError, TimeoutError) as err:
            raise RDTClientError("Unable to contact RDT-Client login") from err
        if not accepted:
            self._logged_in = False
            raise RDTClientAuthenticationError("RDT-Client rejected credentials")
        self._logged_in = True
        self._auth_generation += 1

    async def _get_once(self, path: str) -> Any:
        try:
            async with self.session.get(
                f"{self.base_url}{path}",
                allow_redirects=False,
                timeout=ClientTimeout(total=15),
            ) as response:
                if 300 <= response.status < 400:
                    raise RDTClientError("RDT-Client API redirect refused")
                if response.status in (401, 403):
                    raise RDTClientAuthenticationError("RDT-Client session unauthorized")
                response.raise_for_status()
                return await response.json()
        except RDTClientAuthenticationError:
            raise
        except (ClientError, TimeoutError, ContentTypeError, ValueError) as err:
            raise RDTClientError(f"Unable to retrieve {path}") from err

    async def _get_json(self, path: str) -> Any:
        if not self._logged_in:
            # The lock and double-check prevent a burst of first-time requests
            # from sending the same credentials repeatedly.
            async with self._auth_lock:
                if not self._logged_in:
                    await self._login_unlocked()
        generation = self._auth_generation
        try:
            return await self._get_once(path)
        except RDTClientAuthenticationError:
            # If another request has already renewed the cookie, reuse it.
            # Only one renewal per auth generation may occur.
            async with self._auth_lock:
                if self._auth_generation == generation:
                    self._logged_in = False
                    await self._login_unlocked()
            return await self._get_once(path)

    async def get_transfer_info(self) -> dict[str, Any]:
        """Return global transfer data; numeric units still need verification."""
        result = await self._get_json(API_TRANSFER_INFO)
        if not isinstance(result, dict):
            raise RDTClientError("Unexpected transfer response format")
        return result

    async def get_torrents(self) -> list[dict[str, Any]]:
        """Return queued torrents; an empty queue is valid."""
        result = await self._get_json(API_TORRENTS_INFO)
        if not isinstance(result, list) or any(not isinstance(x, dict) for x in result):
            raise RDTClientError("Unexpected torrent response format")
        return result

    async def get_provider_profile(self) -> dict[str, Any]:
        """Read provider premium/expiry metadata without logging account details."""
        result = await self._get_json(API_PROVIDER_PROFILE)
        if not isinstance(result, dict):
            raise RDTClientError("Unexpected provider profile response format")
        return result
