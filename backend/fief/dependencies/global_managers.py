from fastapi import Depends

from fief.db import AsyncSession, get_global_async_session
from fief.managers import (
    AccountManager,
    AccountUserManager,
    AdminSessionTokenManager,
    get_manager,
)


async def get_account_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> AccountManager:
    return get_manager(AccountManager, session)


async def get_admin_session_token_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> AdminSessionTokenManager:
    return get_manager(AdminSessionTokenManager, session)


async def get_account_user_manager(
    session: AsyncSession = Depends(get_global_async_session),
) -> AccountUserManager:
    return get_manager(AccountUserManager, session)
