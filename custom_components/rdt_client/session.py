"""A dedicated, explicitly owned HTTP session for RDT-Client.

Do not use Home Assistant's shared session for per-server credentials/cookies.
Each integration entry and setup validation owns and closes its own session.
"""
from aiohttp import ClientSession, CookieJar, TCPConnector


def create_rdt_session(*, verify_ssl: bool = True) -> ClientSession:
    """Create an isolated cookie jar and TLS-configured connection pool."""
    return ClientSession(
        cookie_jar=CookieJar(unsafe=True),
        connector=TCPConnector(ssl=verify_ssl),
        trust_env=False,
    )
