from fastapi import Depends

from fief.db import AsyncSession, get_global_async_session
from fief.managers import AccountManager, get_manager


async def get_account_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> AccountManager:
    return get_manager(AccountManager, session)
