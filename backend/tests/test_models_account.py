import pytest

from fief.db import AsyncSession
from fief.models import Account


@pytest.mark.asyncio
async def test_create_account(main_session: AsyncSession):
    account = Account(name="Duché de Bretagne", domain="bretagne.fief.dev")
    main_session.add(account)

    await main_session.commit()

    account_db = await main_session.get(Account, account.id)
    assert account_db is not None
