"""Pure subscription helpers for RDT-Client profile data.

No network calls, Home Assistant dependencies, or private account fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil


def parse_expiration(value: object) -> datetime | None:
    """Return an aware UTC datetime for a valid ISO-8601 timestamp.

    A missing, malformed or timezone-naive value is treated as unknown.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def days_until_expiration(
    expiration: datetime | None, *, now: datetime | None = None
) -> int | None:
    """Return days remaining, rounding partial days up; zero if expired.

    None means the expiration is unknown. Both datetimes must be aware.
    """
    if expiration is None:
        return None
    current = datetime.now(timezone.utc) if now is None else now
    if expiration.tzinfo is None or current.tzinfo is None:
        raise ValueError("Expiration and current time must be timezone-aware")
    remaining_seconds = (expiration - current).total_seconds()
    return max(0, ceil(remaining_seconds / 86400))
