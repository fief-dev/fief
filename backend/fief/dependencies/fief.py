from typing import Optional

from fastapi import Header
from fief_client import FiefAsync

from fief.settings import settings


async def get_fief(
    host: Optional[str] = Header(None, include_in_schema=False)
) -> FiefAsync:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return FiefAsync(
        settings.fief_base_url,
        settings.fief_client_id,
        settings.fief_client_secret,
        encryption_key=settings.fief_encryption_key,
        host=host,
    )
