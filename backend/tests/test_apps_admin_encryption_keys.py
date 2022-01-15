import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.db import AsyncSession
from fief.managers import AccountManager
from fief.models import Account


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestCreateEncryptionKey:
    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        account: Account,
        global_session: AsyncSession,
    ):
        response = await test_client_admin.post("/encryption-keys/")

        assert response.status_code == status.HTTP_201_CREATED

        key = jwk.JWK.from_json(response.text)

        assert key.has_private == True
        assert key.has_public == True

        manager = AccountManager(global_session)
        updated_account = await manager.get_by_id(account.id)
        assert updated_account is not None
        assert updated_account.encrypt_jwk is not None

        account_key = jwk.JWK.from_json(updated_account.encrypt_jwk)
        assert account_key.has_private == False
        assert account_key.has_public == True
