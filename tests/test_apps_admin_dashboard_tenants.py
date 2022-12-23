import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.models import Client
from fief.repositories import ClientRepository, TenantRepository
from tests.data import TestData
from tests.helpers import admin_dashboard_unauthorized_assertions


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListTenants:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/tenants/")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            "/tenants/", headers={"HX-Request": "true", "HX-Combobox": "true"}
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["tenants"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/tenants/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["tenants"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetTenant:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            f"/tenants/{test_data['tenants']['default'].id}"
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(
            f"/tenants/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.get(f"/tenants/{tenant.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert tenant.name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateTenant:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.post("/tenants/create", data={})

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/tenants/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/tenants/create",
            data={
                "name": "Tertiary",
                "registration_allowed": True,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        tenant_repository = TenantRepository(workspace_session)
        tenant = await tenant_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert tenant is not None
        assert tenant.name == "Tertiary"
        assert tenant.registration_allowed is True
        assert tenant.slug == "tertiary"
        assert tenant.default is False

        client_repository = ClientRepository(workspace_session)
        clients = await client_repository.list(
            select(Client).where(Client.tenant_id == tenant.id)
        )
        assert len(clients) == 1

        client = clients[0]
        assert client.first_party is True
        assert client.redirect_uris == ["http://localhost:8000/docs/oauth2-redirect"]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateTenant:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            f"/tenants/{tenant.id}/edit", data={}
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.post(
            f"/tenants/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "name": "Updated name",
                "registration_allowed": tenant.registration_allowed,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        tenant_repository = TenantRepository(workspace_session)
        updated_tenant = await tenant_repository.get_by_id(tenant.id)
        assert updated_tenant is not None
        assert updated_tenant.name == "Updated name"
