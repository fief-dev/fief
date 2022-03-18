from fief_client import FiefAsync

from fief.settings import settings

fief = FiefAsync(
    settings.fief_base_url,
    settings.fief_client_id,
    settings.fief_client_secret,
    encryption_key=settings.fief_encryption_key,
)


async def get_fief() -> FiefAsync:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return fief
