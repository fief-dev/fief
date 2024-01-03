import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import RoleRepository
from fief.tasks import on_role_updated
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion, unordered_list


@pytest.mark.asyncio
class TestListRoles:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/access-control/roles/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get(
            "/access-control/roles/",
            headers={"HX-Request": "true", "HX-Combobox": "true"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["roles"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/access-control/roles/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["roles"])


@pytest.mark.asyncio
class TestGetRole:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/access-control/roles/{test_data['roles']['castles_visitor'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/access-control/roles/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.get(f"/access-control/roles/{role.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert role.name in title.text


@pytest.mark.asyncio
class TestCreateRole:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.post(
            "/access-control/roles/create", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/access-control/roles/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing_permission(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        response = await test_client_dashboard.post(
            "/access-control/roles/create",
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
        test_client_dashboard: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        response = await test_client_dashboard.post(
            "/access-control/roles/create",
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

        role_repository = RoleRepository(main_session)
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
class TestUpdateRole:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.post(
            f"/access-control/roles/{role.id}/edit", data={}
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
            f"/access-control/roles/{not_existing_uuid}/edit", data={}
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
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.post(
            f"/access-control/roles/{role.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing_permission(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
        csrf_token: str,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.post(
            f"/access-control/roles/{role.id}/edit",
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
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        main_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.post(
            f"/access-control/roles/{role.id}/edit",
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

        role_repository = RoleRepository(main_session)
        updated_role = await role_repository.get_by_id(role.id)
        assert updated_role is not None
        assert updated_role.name == "Updated name"

        assert len(updated_role.permissions) == 2
        permission_ids = [permission.id for permission in updated_role.permissions]
        assert test_data["permissions"]["castles:create"].id in permission_ids
        assert test_data["permissions"]["castles:update"].id in permission_ids

        send_task_mock.assert_called_with(
            on_role_updated,
            str(role.id),
            unordered_list(
                [
                    str(test_data["permissions"]["castles:update"].id),
                    str(test_data["permissions"]["castles:create"].id),
                ]
            ),
            unordered_list([str(test_data["permissions"]["castles:read"].id)]),
        )


@pytest.mark.asyncio
class TestDeleteRole:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.delete(
            f"/access-control/roles/{role.id}/delete"
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
            f"/access-control/roles/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.get(
            f"/access-control/roles/{role.id}/delete"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://api.fief.dev/access-control/roles/{role.id}/delete"
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
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_dashboard.delete(
            f"/access-control/roles/{role.id}/delete"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
