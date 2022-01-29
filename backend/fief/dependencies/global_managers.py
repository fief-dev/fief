from fastapi import Depends

from fief.db import AsyncSession, get_global_async_session
from fief.managers import AccountManager, SessionTokenManager, get_manager


async def get_account_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> AccountManager:
    return get_manager(AccountManager, session)


async def get_session_token_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> SessionTokenManager:
    return get_manager(SessionTokenManager, session)
