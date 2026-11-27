"""UI configuration flow for RDT-Client.

Prototype: the integration still needs an entry setup/coordinator before
this can be used as a fully functional Home Assistant integration.
"""

from __future__ import annotations

from urllib.parse import urlsplit

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import RDTClientAPI, RDTClientAuthenticationError, RDTClientError
from .const import DOMAIN
from .config_url import normalize_server_url
from .session import create_rdt_session


class RDTClientConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Guide the user through RDT-Client connection setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Show setup form and validate the connection before saving."""
        errors = {}

        if user_input is not None:
            try:
                url = normalize_server_url(user_input[CONF_URL])
            except ValueError:
                errors["base"] = "invalid_url"
            else:
                # Use a dedicated cookie jar for IP-address hosts.
                # This temporary validation session must be closed after use.
                session = create_rdt_session(
                    verify_ssl=user_input.get(CONF_VERIFY_SSL, True)
                )
                try:
                    api = RDTClientAPI(
                        session=session,
                        base_url=url,
                        username=user_input[CONF_USERNAME],
                        password=user_input[CONF_PASSWORD],
                    )
                    await api.get_transfer_info()
                except RDTClientAuthenticationError:
                    errors["base"] = "invalid_auth"
                except RDTClientError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    # Avoid leaking sensitive URLs/credentials in logs.
                    errors["base"] = "unknown"
                finally:
                    await session.close()

                if not errors:
                    await self.async_set_unique_id(url.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"RDT-Client ({urlsplit(url).hostname})",
                        data={
                            CONF_URL: url,
                            CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, True),
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Optional(CONF_VERIFY_SSL, default=True): bool,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )
