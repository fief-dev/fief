import pytest

from fief.db import AsyncSession
from fief.models import Account


@pytest.mark.asyncio
async def test_create_account(global_session: AsyncSession):
    account = Account(name="Duché de Bretagne", domain="bretagne.fief.dev")
    global_session.add(account)

    await global_session.commit()

    account_db = await global_session.get(Account, account.id)
    assert account_db is not None
