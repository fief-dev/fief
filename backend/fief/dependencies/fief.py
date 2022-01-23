from fief_client.client import Fief

from fief.settings import settings


async def get_fief() -> Fief:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return Fief(
        settings.fief_domain,
        settings.fief_client_id,
        settings.fief_client_secret,
        settings.fief_encryption_key,
    )
