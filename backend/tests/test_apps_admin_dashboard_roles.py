import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import RoleRepository
from fief.tasks import on_role_updated
from tests.data import TestData
from tests.helpers import admin_dashboard_unauthorized_assertions


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListRoles:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/roles/")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            "/roles/", headers={"HX-Request": "true", "HX-Combobox": "true"}
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["roles"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/roles/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["roles"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetRole:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            f"/roles/{test_data['roles']['castles_visitor'].id}"
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(f"/roles/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.get(f"/roles/{role.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert role.name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateRole:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.post("/roles/create", data={})

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/roles/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing_permission(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/roles/create",
            data={
                "name": "New role",
                "granted_by_default": False,
                "permissions": [str(not_existing_uuid)],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_permission"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/roles/create",
            data={
                "name": "New role",
                "granted_by_default": False,
                "permissions": [
                    str(test_data["permissions"]["castles:read"].id),
                    str(test_data["permissions"]["castles:create"].id),
                ],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        role_repository = RoleRepository(workspace_session)
        role = await role_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert role is not None
        assert role.name == "New role"
        assert role.granted_by_default is False

        assert len(role.permissions) == 2
        permission_ids = [permission.id for permission in role.permissions]
        assert test_data["permissions"]["castles:read"].id in permission_ids
        assert test_data["permissions"]["castles:create"].id in permission_ids


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateRole:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.post(
            f"/roles/{role.id}/edit", data={}
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
            f"/roles/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.post(
            f"/roles/{role.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing_permission(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.post(
            f"/roles/{role.id}/edit",
            data={
                "name": "Updated name",
                "granted_by_default": False,
                "permissions": [str(not_existing_uuid)],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "unknown_permission"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
        workspace: Workspace,
        send_task_mock: MagicMock,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.post(
            f"/roles/{role.id}/edit",
            data={
                "name": "Updated name",
                "granted_by_default": True,
                "permissions": [
                    str(test_data["permissions"]["castles:create"].id),
                    str(test_data["permissions"]["castles:update"].id),
                ],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        role_repository = RoleRepository(workspace_session)
        updated_role = await role_repository.get_by_id(role.id)
        assert updated_role is not None
        assert updated_role.name == "Updated name"

        assert len(updated_role.permissions) == 2
        permission_ids = [permission.id for permission in updated_role.permissions]
        assert test_data["permissions"]["castles:create"].id in permission_ids
        assert test_data["permissions"]["castles:update"].id in permission_ids

        send_task_mock.assert_called_once()
        assert send_task_mock.call_args[0][0] == on_role_updated
        assert send_task_mock.call_args[0][1] == str(role.id)
        assert set(send_task_mock.call_args[0][2]) == {
            str(test_data["permissions"]["castles:create"].id),
            str(test_data["permissions"]["castles:update"].id),
        }
        assert set(send_task_mock.call_args[0][3]) == {
            str(test_data["permissions"]["castles:read"].id)
        }
        assert send_task_mock.call_args[0][4] == str(workspace.id)


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteRole:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.delete(f"/roles/{role.id}/delete")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.delete(
            f"/roles/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.get(f"/roles/{role.id}/delete")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={"hx-delete": f"http://{workspace.domain}/roles/{role.id}/delete"},
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_admin_dashboard.delete(f"/roles/{role.id}/delete")

        assert response.status_code == status.HTTP_204_NO_CONTENT