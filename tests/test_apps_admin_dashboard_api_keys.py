import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.crypto.token import generate_token, get_token_hash
from fief.db import AsyncSession
from fief.models import AdminAPIKey, Workspace
from fief.repositories import AdminAPIKeyRepository
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListAPIKeys:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.get("/api-keys/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/api-keys/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == 1


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateAPIKey:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.post("/api-keys/create", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/api-keys/create", data={"csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        main_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/api-keys/create", data={"name": "New API Key", "csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_201_CREATED

        html = BeautifulSoup(response.text, features="html.parser")
        token = html.find("pre").text.strip()

        api_key_repository = AdminAPIKeyRepository(main_session)
        api_key = await api_key_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert api_key is not None
        assert api_key.token == get_token_hash(token)


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteAPIKey:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        admin_api_key: tuple[AdminAPIKey, str],
    ):
        response = await test_client_admin_dashboard.delete(
            f"/api-keys/{admin_api_key[0].id}/delete"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing_api_key(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.delete(
            f"/api-keys/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        main_session: AsyncSession,
        workspace: Workspace,
    ):
        api_key_repository = AdminAPIKeyRepository(main_session)
        _, token_hash = generate_token()
        api_key = AdminAPIKey(
            name="New API Key", token=token_hash, workspace_id=workspace.id
        )
        api_key = await api_key_repository.create(api_key)

        response = await test_client_admin_dashboard.get(
            f"/api-keys/{api_key.id}/delete"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://{workspace.domain}/api-keys/{api_key.id}/delete"
            },
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        main_session: AsyncSession,
        workspace: Workspace,
    ):
        api_key_repository = AdminAPIKeyRepository(main_session)
        _, token_hash = generate_token()
        api_key = AdminAPIKey(
            name="New API Key", token=token_hash, workspace_id=workspace.id
        )
        api_key = await api_key_repository.create(api_key)

        response = await test_client_admin_dashboard.delete(
            f"/api-keys/{api_key.id}/delete"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
