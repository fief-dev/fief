import uuid

import httpx
import pytest
from fastapi import status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.models import Client
from fief.repositories import ClientRepository
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListTenants:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/tenants/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/tenants/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["tenants"])

    @pytest.mark.authenticated_admin
    @pytest.mark.parametrize(
        "query,nb_results",
        [("default", 1), ("de", 1), ("SECONDARY", 1), ("unknown", 0)],
    )
    async def test_query_filter(
        self, query: str, nb_results: int, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.get("/tenants/", params={"query": query})

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == nb_results


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateTenant:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/tenants/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, workspace_session: AsyncSession
    ):
        response = await test_client_admin.post("/tenants/", json={"name": "Tertiary"})

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["name"] == "Tertiary"
        assert json["slug"] == "tertiary"
        assert json["default"] is False

        client_repository = ClientRepository(workspace_session)
        clients = await client_repository.list(
            select(Client).where(Client.tenant_id == uuid.UUID(json["id"]))
        )
        assert len(clients) == 1

        client = clients[0]
        assert client.first_party is True
        assert client.redirect_uris == ["http://localhost:8000/docs/oauth2-redirect"]

    @pytest.mark.authenticated_admin
    async def test_slug_collision(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/tenants/", json={"name": "Secondary"})

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["name"] == "Secondary"
        assert json["slug"] != "secondary"
        assert json["slug"].startswith("secondary")

    @pytest.mark.authenticated_admin
    async def test_unknown_theme(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.post(
            "/tenants/",
            json={"name": "Tertiary", "theme_id": str(not_existing_uuid)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json = response.json()
        assert json["detail"] == APIErrorCode.TENANT_CREATE_NOT_EXISTING_THEME

    @pytest.mark.parametrize("theme_alias", [None, "custom"])
    @pytest.mark.authenticated_admin
    async def test_valid_theme(
        self,
        theme_alias: str | None,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        theme_id: str | None = (
            str(test_data["themes"][theme_alias].id)
            if theme_alias is not None
            else None
        )
        response = await test_client_admin.post(
            "/tenants/",
            json={"name": "Tertiary", "theme_id": theme_id},
        )

        assert response.status_code == status.HTTP_201_CREATED
        json = response.json()
        assert json["theme_id"] == theme_id


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateTenant:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.patch(f"/tenants/{tenant.id}", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.patch(
            f"/tenants/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.patch(
            f"/tenants/{tenant.id}",
            json={"name": "Updated name"},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["name"] == "Updated name"

    @pytest.mark.authenticated_admin
    async def test_unknown_theme(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.patch(
            f"/tenants/{tenant.id}",
            json={"theme_id": str(not_existing_uuid)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json = response.json()
        assert json["detail"] == APIErrorCode.TENANT_UPDATE_NOT_EXISTING_THEME

    @pytest.mark.parametrize("theme_alias", [None, "custom"])
    @pytest.mark.authenticated_admin
    async def test_valid_theme(
        self,
        theme_alias: str | None,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        theme_id: str | None = (
            str(test_data["themes"][theme_alias].id)
            if theme_alias is not None
            else None
        )
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.patch(
            f"/tenants/{tenant.id}",
            json={"theme_id": theme_id},
        )

        assert response.status_code == status.HTTP_200_OK
        json = response.json()
        assert json["theme_id"] == theme_id
