"""Read-only, privacy-preserving RDT-Client transfer summaries.

Uses qBittorrent-compatible transfer and torrent fields. Never exposes names,
hashes, paths, tracker URLs, or other torrent metadata to Home Assistant.
"""

from __future__ import annotations

from typing import Any


def _nonnegative_integer(value: Any) -> int | None:
    """Reject invalid, negative, boolean, or non-integral measurements."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def summarize_downloads(
    transfer: dict[str, Any], torrents: list[dict[str, Any]]
) -> dict[str, int | None]:
    """Return sanitized aggregate transfer counters and reported speeds."""
    if not isinstance(transfer, dict):
        raise ValueError("Transfer payload must be an object")
    if not isinstance(torrents, list) or any(
        not isinstance(item, dict) for item in torrents
    ):
        raise ValueError("Torrent payload must be a list of objects")

    downloading_states = {"downloading", "forcedDL", "metaDL", "stalledDL"}
    queued_states = {"queuedDL", "checkingDL", "allocating", "checkingResumeData"}

    downloading = sum(item.get("state") in downloading_states for item in torrents)
    queued = sum(item.get("state") in queued_states for item in torrents)
    return {
        "download_speed": _nonnegative_integer(transfer.get("dl_info_speed")),
        "upload_speed": _nonnegative_integer(transfer.get("up_info_speed")),
        "torrent_count": len(torrents),
        "downloading_count": downloading,
        "queued_count": queued,
    }

