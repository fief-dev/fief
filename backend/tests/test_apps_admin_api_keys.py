import uuid

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.managers import AdminAPIKeyManager
from fief.models import Account, AdminAPIKey


@pytest.mark.asyncio
@pytest.mark.account_host()
class TestListAPIKeys:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/api-keys/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.get("/api-keys/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, admin_api_key: AdminAPIKey
    ):
        response = await test_client_admin.get("/api-keys/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 1

        for result in json["results"]:
            assert result["token"] == "**********"


@pytest.mark.asyncio
@pytest.mark.account_host()
class TestCreateAPIKey:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/api-keys/", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.post("/api-keys/", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(self, test_client_admin: httpx.AsyncClient, account: Account):
        response = await test_client_admin.post(
            "/api-keys/", json={"name": "New API Key"}
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["token"] != "**********"
        assert json["account_id"] == str(account.id)


@pytest.mark.asyncio
@pytest.mark.account_host()
class TestDeleteAPIKey:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, admin_api_key: AdminAPIKey
    ):
        response = await test_client_admin.delete(f"/api-keys/{admin_api_key.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient, admin_api_key: AdminAPIKey
    ):
        response = await test_client_admin.delete(f"/api-keys/{admin_api_key.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing_api_key(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.delete(f"/api-keys/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self,
        test_client_admin: httpx.AsyncClient,
        global_session: AsyncSession,
        account: Account,
    ):
        api_key_manager = AdminAPIKeyManager(global_session)
        api_key = AdminAPIKey(name="New API Key", account_id=account.id)
        api_key = await api_key_manager.create(api_key)

        response = await test_client_admin.delete(f"/api-keys/{api_key.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        deleted_api_key = await api_key_manager.get_by_id(api_key.id)
        assert deleted_api_key is None
