"""Strict URL validation shared by setup and API client."""

from __future__ import annotations

from urllib.parse import urlsplit


def normalize_server_url(url: str) -> str:
    """Allow HTTP(S) origins only; never embed credentials or request paths."""
    if not isinstance(url, str):
        raise ValueError("Invalid RDT-Client server URL")
    value = url.strip()
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value)
            or "\\" in value
            or "@" in parsed.netloc
            or "%" in parsed.netloc
        ):
            raise ValueError
        port = parsed.port  # Reject malformed/out-of-range port.
        if port == 0:
            raise ValueError
        # Reject malformed hosts and Unicode URL ambiguity.
        if not parsed.hostname.isascii():
            raise ValueError
    except ValueError as err:
        raise ValueError("Invalid RDT-Client server URL") from err
    return value.rstrip("/")
