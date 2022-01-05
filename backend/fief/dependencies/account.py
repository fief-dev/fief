from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends
from pydantic import UUID4

from fief.db import AsyncEngine, AsyncSession, create_async_session_maker, create_engine
from fief.dependencies.global_managers import get_account_manager
from fief.managers import AccountManager
from fief.models import Account


async def get_current_account(
    account_id: UUID4 = Header(..., alias="x-fief-account"),
    manager: AccountManager = Depends(get_account_manager),
) -> Account:
    account = await manager.get_by_id(account_id)

    if account is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return account


@lru_cache
def get_engine(database_url: str) -> AsyncEngine:
    return create_engine(database_url)


async def get_current_account_engine(
    account: Account = Depends(get_current_account),
) -> AsyncEngine:
    return get_engine(account.get_database_url())


async def get_current_account_session(
    engine: AsyncEngine = Depends(get_current_account_engine),
) -> AsyncGenerator[AsyncSession, None]:
    session_maker = create_async_session_maker(engine)
    yield session_maker()
