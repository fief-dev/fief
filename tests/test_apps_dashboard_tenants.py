import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.models import Client, Workspace
from fief.repositories import ClientRepository, TenantRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListTenants:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/tenants/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get(
            "/tenants/", headers={"HX-Request": "true", "HX-Combobox": "true"}
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["tenants"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/tenants/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["tenants"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetTenant:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/tenants/{test_data['tenants']['default'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(f"/tenants/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.get(f"/tenants/{tenant.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert tenant.name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateTenant:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.post("/tenants/create", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/tenants/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_logo_url(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/tenants/create",
            data={
                "name": "Tertiary",
                "registration_allowed": True,
                "logo_url": "INVALID_URL",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_theme(
        self,
        test_client_dashboard: httpx.AsyncClient,
        csrf_token: str,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            "/tenants/create",
            data={
                "name": "Tertiary",
                "registration_allowed": True,
                "theme": not_existing_uuid,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_theme"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_oauth_provider(
        self,
        test_client_dashboard: httpx.AsyncClient,
        csrf_token: str,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            "/tenants/create",
            data={
                "name": "Tertiary",
                "registration_allowed": True,
                "oauth_providers": [str(not_existing_uuid)],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_oauth_provider"

    @pytest.mark.parametrize("theme_alias", [None, "custom"])
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        theme_alias: str | None,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        theme_id: str | None = (
            str(test_data["themes"][theme_alias].id)
            if theme_alias is not None
            else None
        )
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.post(
            "/tenants/create",
            data={
                "name": "Tertiary",
                "registration_allowed": True,
                "theme": theme_id,
                "oauth_providers": [str(oauth_provider.id)],
                "logo_url": "https://bretagne.duchy/logo.svg",
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
        assert tenant.logo_url == "https://bretagne.duchy/logo.svg"
        if theme_id is None:
            assert tenant.theme_id is None
        else:
            assert tenant.theme_id == uuid.UUID(theme_id)

        assert len(tenant.oauth_providers) == 1
        assert tenant.oauth_providers[0].id == oauth_provider.id

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
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            f"/tenants/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_logo_url(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "name": "Updated name",
                "registration_allowed": tenant.registration_allowed,
                "logo_url": "INVALID_URL",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_theme(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "name": "Updated name",
                "registration_allowed": tenant.registration_allowed,
                "theme": not_existing_uuid,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_theme"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_oauth_provider(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "name": "Updated name",
                "registration_allowed": tenant.registration_allowed,
                "oauth_providers": [not_existing_uuid],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_oauth_provider"

    @pytest.mark.parametrize("theme_alias", [None, "custom"])
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        theme_alias: str | None,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        theme_id: str | None = (
            str(test_data["themes"][theme_alias].id)
            if theme_alias is not None
            else None
        )
        oauth_provider = test_data["oauth_providers"]["google"]
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            f"/tenants/{tenant.id}/edit",
            data={
                "name": "Updated name",
                "registration_allowed": tenant.registration_allowed,
                "logo_url": "https://bretagne.duchy/logo.svg",
                "theme": theme_id,
                "oauth_providers": [str(oauth_provider.id)],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        tenant_repository = TenantRepository(workspace_session)
        updated_tenant = await tenant_repository.get_by_id(tenant.id)
        assert updated_tenant is not None
        assert updated_tenant.name == "Updated name"
        assert updated_tenant.logo_url == "https://bretagne.duchy/logo.svg"
        if theme_id is None:
            assert updated_tenant.theme_id is None
        else:
            assert updated_tenant.theme_id == uuid.UUID(theme_id)

        assert len(updated_tenant.oauth_providers) == 1
        assert updated_tenant.oauth_providers[0].id == oauth_provider.id


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteTenant:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.delete(f"/tenants/{tenant.id}/delete")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.delete(
            f"/tenants/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.get(f"/tenants/{tenant.id}/delete")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://{workspace.domain}/tenants/{tenant.id}/delete"
            },
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.delete(f"/tenants/{tenant.id}/delete")

        assert response.status_code == status.HTTP_204_NO_CONTENT
