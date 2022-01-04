import pytest

from fief.db import AsyncSession
from fief.models import Account


@pytest.mark.asyncio
async def test_create_account(test_async_session: AsyncSession):
    account = Account(name="Duché de Bretagne", database_url="")
    test_async_session.add(account)

    await test_async_session.commit()

    account_db = await test_async_session.get(Account, account.id)
    assert account_db is not None
