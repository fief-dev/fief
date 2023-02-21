import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import OAuthProviderRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListOAuthProviders:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/oauth-providers/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/oauth-providers/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["oauth_providers"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetOAuthProvider:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/oauth-providers/{test_data['oauth_providers']['google'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/oauth-providers/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.get(
            f"/oauth-providers/{oauth_provider.id}"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert oauth_provider.display_name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateOAuthProvider:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.post("/oauth-providers/create", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.parametrize(
        "provider,has_field", [("GOOGLE", False), ("OPENID", True)]
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_openid_configuration_endpoint_field_display(
        self,
        provider: str,
        has_field: bool,
        test_client_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_dashboard.post(
            "/oauth-providers/create",
            data={
                "provider": provider,
                "csrf_token": csrf_token,
            },
            headers={"HX-Trigger": "change"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        field = html.find("input", id="openid_configuration_endpoint")
        if has_field:
            assert field is not None
        else:
            assert field is None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/oauth-providers/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_missing_configuration_endpoint_for_openid(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/oauth-providers/create",
            data={
                "provider": "OPENID",
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                "scopes-0": "openid",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "payload",
        [
            {"provider": "GOOGLE", "scopes-0": "openid"},
            {
                "provider": "OPENID",
                "openid_configuration_endpoint": "http://rome.city/.well-known/openid-configuration",
                "scopes-0": "openid",
            },
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        payload: dict[str, str],
        test_client_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        response = await test_client_dashboard.post(
            "/oauth-providers/create",
            data={
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                **payload,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        oauth_provider_repository = OAuthProviderRepository(workspace_session)
        oauth_provider = await oauth_provider_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert oauth_provider is not None
        assert oauth_provider.provider == payload["provider"]
        assert oauth_provider.client_id == "CLIENT_ID"
        assert oauth_provider.client_secret == "CLIENT_SECRET"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateOAuthProvider:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.post(
            f"/oauth-providers/{oauth_provider.id}/edit", data={}
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
            f"/oauth-providers/{not_existing_uuid}/edit", data={}
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
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.post(
            f"/oauth-providers/{oauth_provider.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_cant_update_provider(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.post(
            f"/oauth-providers/{oauth_provider.id}/edit",
            data={
                "provider": "GITHUB",
                "name": oauth_provider.name,
                "client_id": oauth_provider.client_id,
                "client_secret": oauth_provider.client_secret,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        oauth_provider_repository = OAuthProviderRepository(workspace_session)
        updated_oauth_provider = await oauth_provider_repository.get_by_id(
            oauth_provider.id
        )
        assert updated_oauth_provider is not None
        assert updated_oauth_provider.provider == oauth_provider.provider

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.post(
            f"/oauth-providers/{oauth_provider.id}/edit",
            data={
                "name": "Updated name",
                "client_id": oauth_provider.client_id,
                "client_secret": oauth_provider.client_secret,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        oauth_provider_repository = OAuthProviderRepository(workspace_session)
        updated_oauth_provider = await oauth_provider_repository.get_by_id(
            oauth_provider.id
        )
        assert updated_oauth_provider is not None
        assert updated_oauth_provider.name == "Updated name"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteOAuthProvider:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.delete(
            f"/oauth-providers/{oauth_provider.id}/delete"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.delete(
            f"/oauth-providers/{not_existing_uuid}/delete"
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
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.get(
            f"/oauth-providers/{oauth_provider.id}/delete"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://{workspace.domain}/oauth-providers/{oauth_provider.id}/delete"
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
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_dashboard.delete(
            f"/oauth-providers/{oauth_provider.id}/delete"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
