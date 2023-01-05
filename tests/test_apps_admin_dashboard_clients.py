import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status
from jwcrypto import jwk

from fief.db import AsyncSession
from fief.repositories import ClientRepository
from tests.data import TestData
from tests.helpers import admin_dashboard_unauthorized_assertions


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListClients:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/clients/")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            "/clients/", headers={"HX-Request": "true", "HX-Combobox": "true"}
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["clients"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/clients/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["clients"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetClient:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            f"/clients/{test_data['clients']['default_tenant'].id}"
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(
            f"/clients/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.get(f"/clients/{client.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert client.name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateClient:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.post("/clients/create", data={})

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_empty_redirect_uris(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/clients/create",
            data={
                "name": "New client",
                "first_party": True,
                "client_type": "confidential",
                "tenant": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_redirect_uris_not_https(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/clients/create",
            data={
                "name": "New client",
                "first_party": True,
                "client_type": "confidential",
                "redirect_uris-0": "http://nantes.city/callback",
                "tenant": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_tenant(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/clients/create",
            data={
                "name": "New client",
                "first_party": True,
                "client_type": "confidential",
                "redirect_uris-0": "https://nantes.city/callback",
                "tenant": str(not_existing_uuid),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_tenant"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    @pytest.mark.parametrize(
        "redirect_uris",
        [
            ["https://nantes.city/callback"],
            ["http://localhost:8000/callback"],
            ["http://test.localhost:8000/callback"],
            ["http://127.0.0.1:8000/callback"],
        ],
    )
    async def test_valid(
        self,
        redirect_uris: list[str],
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/clients/create",
            data={
                "name": "New client",
                "first_party": True,
                "client_type": "confidential",
                **{
                    f"redirect_uris-{i}": value for i, value in enumerate(redirect_uris)
                },
                "tenant": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        client_repository = ClientRepository(workspace_session)
        client = await client_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert client is not None
        assert client.name == "New client"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateClient:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/edit", data={}
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
            f"/clients/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_redirect_uris_not_https(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/edit",
            data={
                "name": client.name,
                "first_party": client.first_party,
                "client_type": client.client_type.value,
                "redirect_uris-0": "http://nantes.city/callback",
                "tenant": str(client.tenant_id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_cant_update_tenant(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/edit",
            data={
                "name": client.name,
                "first_party": client.first_party,
                "client_type": client.client_type.value,
                **{
                    f"redirect_uris-{i}": value
                    for i, value in enumerate(client.redirect_uris)
                },
                "tenant": str(test_data["tenants"]["secondary"].id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        client_repository = ClientRepository(workspace_session)
        updated_client = await client_repository.get_by_id(client.id)
        assert updated_client is not None
        assert updated_client.tenant_id == client.tenant_id

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/edit",
            data={
                "name": "Updated name",
                "first_party": client.first_party,
                "client_type": client.client_type.value,
                **{
                    f"redirect_uris-{i}": value
                    for i, value in enumerate(client.redirect_uris)
                },
                "tenant": str(client.tenant_id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        client_repository = ClientRepository(workspace_session)
        updated_client = await client_repository.get_by_id(client.id)
        assert updated_client is not None
        assert updated_client.name == "Updated name"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateEncryptionKey:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/encryption-key"
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
            f"/clients/{not_existing_uuid}/encryption-key"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_success(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        client = test_data["clients"]["default_tenant"]
        response = await test_client_admin_dashboard.post(
            f"/clients/{client.id}/encryption-key"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        key_text = html.find("pre").text
        key = jwk.JWK.from_json(key_text)

        assert key.has_private is True
        assert key.has_public is True

        repository = ClientRepository(workspace_session)
        updated_client = await repository.get_by_id(client.id)
        assert updated_client is not None
        assert updated_client.encrypt_jwk is not None

        tenant_key = jwk.JWK.from_json(updated_client.encrypt_jwk)
        assert tenant_key.has_private is False
        assert tenant_key.has_public is True
