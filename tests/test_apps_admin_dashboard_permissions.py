import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import PermissionRepository
from tests.data import TestData
from tests.helpers import admin_dashboard_unauthorized_assertions


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListPermissions:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/access-control/permissions/")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            "/access-control/permissions/",
            headers={"HX-Request": "true", "HX-Combobox": "true"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["permissions"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/access-control/permissions/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["permissions"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_create_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/access-control/permissions/",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_already_existing_codename(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/access-control/permissions/",
            data={
                "name": "New permission",
                "codename": "castles:create",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "permission_codename_already_exists"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_create_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/access-control/permissions/",
            data={
                "name": "New permission",
                "codename": "new_permission",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        permission_repository = PermissionRepository(workspace_session)
        permission = await permission_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert permission is not None
        assert permission.name == "New permission"
        assert permission.codename == "new_permission"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeletePermission:
    async def test_unauthorized(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_admin_dashboard.delete(
            f"/access-control/permissions/{permission.id}/delete"
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.delete(
            f"/access-control/permissions/{not_existing_uuid}/delete"
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
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_admin_dashboard.get(
            f"/access-control/permissions/{permission.id}/delete"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://{workspace.domain}/access-control/permissions/{permission.id}/delete"
            },
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_admin_dashboard.delete(
            f"/access-control/permissions/{permission.id}/delete"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
