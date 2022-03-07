import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.db import AsyncSession
from fief.managers import ClientManager
from tests.data import TestData


@pytest.mark.asyncio
class TestListClients:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/clients/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.admin_session_token()
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/clients/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["clients"])

        for result in json["results"]:
            assert "tenant" in result


@pytest.mark.asyncio
class TestCreateEncryptionKey:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin.post(f"/clients/{client.id}/encryption-key")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.admin_session_token()
    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
        account_session: AsyncSession,
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin.post(f"/clients/{client.id}/encryption-key")

        assert response.status_code == status.HTTP_201_CREATED

        key = jwk.JWK.from_json(response.text)

        assert key.has_private == True
        assert key.has_public == True

        manager = ClientManager(account_session)
        updated_client = await manager.get_by_id(client.id)
        assert updated_client is not None
        assert updated_client.encrypt_jwk is not None

        tenant_key = jwk.JWK.from_json(updated_client.encrypt_jwk)
        assert tenant_key.has_private == False
        assert tenant_key.has_public == True
