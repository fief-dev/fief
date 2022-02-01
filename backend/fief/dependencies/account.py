from typing import AsyncGenerator

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends

from fief.db import AsyncSession, get_account_session
from fief.dependencies.global_managers import get_account_manager
from fief.managers import AccountManager
from fief.models import Account


async def get_current_account(
    host: str = Header(..., include_in_schema=False),
    manager: AccountManager = Depends(get_account_manager),
) -> Account:
    account = await manager.get_by_domain(host)

    if account is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return account


async def get_current_account_session(
    account: Account = Depends(get_current_account),
) -> AsyncGenerator[AsyncSession, None]:
    async with get_account_session(account) as session:
        yield session
