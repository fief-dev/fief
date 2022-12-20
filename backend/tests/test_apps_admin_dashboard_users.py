import datetime
import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import UserRepository
from fief.tasks import on_after_register
from tests.data import TestData
from tests.helpers import admin_dashboard_unauthorized_assertions


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUsers:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/users/")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/users/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["users"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetUser:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            f"/users/{test_data['users']['regular'].id}"
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(f"/users/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.get(f"/users/{user.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert user.email in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUser:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.post("/users/create", data={})

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_tenant(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant_id": str(not_existing_uuid),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_tenant"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_existing_user(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/users/create",
            data={
                "email": "anne@bretagne.duchy",
                "password": "hermine1",
                "tenant_id": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_already_exists"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_password(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "h",
                "tenant_id": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_password"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_field_value(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant_id": str(tenant.id),
                "fields-last_seen": "INVALID_VALUE",
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
        send_task_mock: MagicMock,
        workspace: Workspace,
        workspace_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant_id": str(tenant.id),
                "fields-onboarding_done": True,
                "fields-last_seen": "2022-01-01 13:37:00",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert user is not None
        assert user.email == "louis@bretagne.duchy"
        assert user.tenant_id == tenant.id

        assert user.fields["onboarding_done"] is True
        assert user.fields["last_seen"] == datetime.datetime(
            2022, 1, 1, 12, 37, tzinfo=datetime.timezone.utc
        )

        send_task_mock.assert_called_once_with(
            on_after_register, str(user.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateUser:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/edit", data={}
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
            f"/users/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_existing_email_address(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/edit",
            data={
                "email": "isabeau@bretagne.duchy",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_already_exists"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_password(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/edit",
            data={
                "email": user.email,
                "password": "h",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_password"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_field_value(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/edit",
            data={
                "email": user.email,
                "fields-last_seen": "INVALID_VALUE",
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
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/edit",
            data={
                "email": "anne+updated@bretagne.duchy",
                "password": "hermine1",
                "fields-onboarding_done": True,
                "fields-last_seen": "2022-01-01 13:37:00",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_repository = UserRepository(workspace_session)
        updated_user = await user_repository.get_by_id(user.id)
        assert updated_user is not None
        assert updated_user.email == "anne+updated@bretagne.duchy"

        assert updated_user.fields["onboarding_done"] is True
        assert updated_user.fields["last_seen"] == datetime.datetime(
            2022, 1, 1, 12, 37, tzinfo=datetime.timezone.utc
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserAccessToken:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/access-token", data={}
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
            f"/users/{not_existing_uuid}/access-token", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.get(
            f"/users/{user.id}/access-token"
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_client(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client_id": str(not_existing_uuid),
                "scopes-0": "openid",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_client"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_client_not_in_user_tenant(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client_id": str(test_data["clients"]["secondary_tenant"].id),
                "scopes-0": "openid",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_client"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client_id": str(test_data["clients"]["default_tenant"].id),
                "scopes-0": "openid",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        access_token = html.find("pre").text
        assert access_token is not None
