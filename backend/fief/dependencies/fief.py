from typing import Any, Dict
from urllib.parse import urlsplit, urlunsplit

from fief_client import FiefAsync

from fief.settings import settings


class FiefAsyncRelativeEndpoints(FiefAsync):
    def _get_endpoint_url(
        self, openid_configuration: Dict[str, Any], field: str
    ) -> str:
        """
        Tweak the URL so they are relative instead of absolute.

        Fief will always return absolute URL on the .well-known endpoint.

        For the Fief-ception, we always need to call them from localhost,
        so we just get rid of the scheme and host part.

        The only exception is `authorization_endpoint`:
        in this case, we want it to be absolute because it's returned to the
        user and loaded by its browser on the outside.
        """
        netloc = settings.fief_domain if field == "authorization_endpoint" else ""
        url = super()._get_endpoint_url(openid_configuration, field)
        return urlunsplit(("", netloc, *urlsplit(url)[2:]))


fief = FiefAsyncRelativeEndpoints(
    f"http://localhost:{settings.port}",  # Always call Fief on localhost
    settings.fief_client_id,
    settings.fief_client_secret,
    encryption_key=settings.fief_encryption_key,
    host=settings.fief_domain,  # Manually set the host so the workspace is recognized
)


async def get_fief() -> FiefAsyncRelativeEndpoints:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return fief
