"""Privacy-safe qBittorrent-style completion timestamps for RDT-Client.

Use only a reported completion_on Unix timestamp. A poll time, download state,
zero-byte queue, or disappearance from the queue is NOT proof of completion.
No filename, torrent hash, save path or private metadata is retained.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def most_recent_completion(
    torrents: list[dict[str, Any]], *, now: datetime | None = None
) -> datetime | None:
    """Return the latest valid reported completion time, or unknown.

    RDT-Client's live non-empty queue schema has not yet been verified.
    A missing completion_on field therefore remains unknown; never fabricate
    the current polling time as a completed download.
    """
    if not isinstance(torrents, list) or any(
        not isinstance(item, dict) for item in torrents
    ):
        raise ValueError("Unexpected torrent response shape")

    current = datetime.now(timezone.utc) if now is None else now
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("Current time must be timezone-aware")
    latest: datetime | None = None
    for torrent in torrents:
        raw = torrent.get("completion_on")
        if type(raw) is not int or raw <= 0:
            continue
        try:
            candidate = datetime.fromtimestamp(raw, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            continue
        if candidate > current:
            continue
        if latest is None or candidate > latest:
            latest = candidate
    return latest
