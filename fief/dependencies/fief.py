from fief_client import FiefAsync

from fief.settings import settings

fief = FiefAsync(
    f"http://localhost:{settings.port}",  # Always call Fief on localhost
    settings.fief_client_id,
    settings.fief_client_secret,
    encryption_key=settings.fief_encryption_key,
    host=settings.fief_domain,
)


async def get_fief() -> FiefAsync:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return fief
