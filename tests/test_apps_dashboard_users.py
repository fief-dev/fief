import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import (
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.tasks import on_after_register, on_user_role_created, on_user_role_deleted
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUsers:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/users/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/users/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["users"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetUser:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/users/{test_data['users']['regular'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(f"/users/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert user.email in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUser:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.post("/users/create", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_tenant(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        response = await test_client_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant": str(not_existing_uuid),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_tenant"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_existing_user(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            "/users/create",
            data={
                "email": "anne@bretagne.duchy",
                "password": "hermine1",
                "tenant": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_already_exists"

    @pytest.mark.parametrize(
        "password",
        [
            pytest.param("h", id="Too short password"),
            pytest.param("h" * 512, id="Too long password"),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_password(
        self,
        password: str,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": password,
                "tenant": str(tenant.id),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_password"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_field_value(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant": str(tenant.id),
                "fields-last_seen": "INVALID_VALUE",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        send_task_mock: MagicMock,
        workspace: Workspace,
        workspace_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_dashboard.post(
            "/users/create",
            data={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "tenant": str(tenant.id),
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
        assert user.fields["last_seen"] is not None

        send_task_mock.assert_called_with(
            on_after_register, str(user.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateUser:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(f"/users/{user.id}/edit", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            f"/users/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_existing_email_address(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
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
        assert updated_user.fields["last_seen"] is not None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserAccessToken:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/access-token", data={}
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
            f"/users/{not_existing_uuid}/access-token", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}/access-token")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_unknown_client(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client": str(not_existing_uuid),
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client": str(test_data["clients"]["secondary_tenant"].id),
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/access-token",
            data={
                "client": str(test_data["clients"]["default_tenant"].id),
                "scopes-0": "openid",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        access_token = html.find("pre").text
        assert access_token is not None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUser:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.delete(f"/users/{user.id}/delete")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.delete(
            f"/users/{not_existing_uuid}/delete"
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
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}/delete")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={"hx-delete": f"http://{workspace.domain}/users/{user.id}/delete"},
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.delete(f"/users/{user.id}/delete")

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserPermissions:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/users/{test_data['users']['regular'].id}/permissions"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/users/{not_existing_uuid}/permissions"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}/permissions")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = (
            html.find("table", id="user-permissions-table").find("tbody").find_all("tr")
        )
        assert len(rows) == len(
            [
                user_role
                for user_role in test_data["user_permissions"].values()
                if user_role.user_id == user.id
            ]
        )

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_permission_unknown(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/permissions",
            data={"permission": str(not_existing_uuid), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_permission"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_permission_already_added(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        permission = test_data["permissions"]["castles:delete"]
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/permissions",
            data={"permission": str(permission.id), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "already_added_permission"

    @pytest.mark.parametrize("permission_alias", ["castles:create", "castles:read"])
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_permission_valid(
        self,
        permission_alias: str,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        permission = test_data["permissions"][permission_alias]
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/permissions",
            data={"permission": str(permission.id), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Force session to expire objects because trigger_webhooks MagicMock retain them in memory
        workspace_session.expire_all()

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id, direct_only=True)
        )
        assert len(user_permissions) == 2
        assert permission.id in [
            user_permission.permission_id for user_permission in user_permissions
        ]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserPermission:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        permission = test_data["permissions"]["castles:delete"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing_user(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:delete"]
        response = await test_client_dashboard.delete(
            f"/users/{not_existing_uuid}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_added_permission(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        permission = test_data["permissions"]["castles:delete"]
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id, direct_only=True)
        )
        assert len(user_permissions) == 0


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserRoles:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/users/{test_data['users']['regular'].id}/roles"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(f"/users/{not_existing_uuid}/roles")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}/roles")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("table", id="user-roles-table").find("tbody").find_all("tr")
        assert len(rows) == len(
            [
                user_role
                for user_role in test_data["user_roles"].values()
                if user_role.user_id == user.id
            ]
        )

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_role_unknown(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/roles",
            data={"role": str(not_existing_uuid), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_role"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_role_already_added(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        role = test_data["roles"]["castles_visitor"]
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/roles",
            data={"role": str(role.id), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "already_added_role"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_create_role_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        role = test_data["roles"]["castles_manager"]
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.post(
            f"/users/{user.id}/roles",
            data={"role": str(role.id), "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Force session to expire objects because trigger_webhooks MagicMock retain them in memory
        workspace_session.expire_all()

        user_role_repository = UserRoleRepository(workspace_session)
        user_roles = await user_role_repository.list(
            user_role_repository.get_by_user_statement(user.id)
        )
        assert len(user_roles) == 2
        assert role.id in [user_role.role_id for user_role in user_roles]

        send_task_mock.assert_called_with(
            on_user_role_created, str(user.id), str(role.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserRole:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/roles/{role.id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing_user(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.delete(
            f"/users/{not_existing_uuid}/roles/{role.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_added_role(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_manager"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/roles/{role.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.delete(
            f"/users/{user.id}/roles/{role.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user_role_repository = UserRoleRepository(workspace_session)
        user_roles = await user_role_repository.list(
            user_role_repository.get_by_user_statement(user.id)
        )
        assert len(user_roles) == 0

        send_task_mock.assert_called_with(
            on_user_role_deleted, str(user.id), str(role.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserOAuthAccounts:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/users/{test_data['users']['regular'].id}/oauth-accounts"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/users/{not_existing_uuid}/oauth-accounts"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_dashboard.get(f"/users/{user.id}/oauth-accounts")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = (
            html.find("table", id="user-oauth-accounts-table")
            .find("tbody")
            .find_all("tr")
        )
        assert len(rows) == len(
            [
                oauth_account
                for oauth_account in test_data["oauth_accounts"].values()
                if oauth_account.user_id == user.id
            ]
        )
