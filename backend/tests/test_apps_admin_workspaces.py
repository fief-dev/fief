from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.models import Workspace
from fief.schemas.user import UserDB
from fief.services.workspace_db import WorkspaceDatabaseConnectionError


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListWorkspaces:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/workspaces/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.get("/workspaces/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client_admin.get("/workspaces/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 1
        assert json["results"][0]["id"] == str(workspace.id)


@pytest.mark.asyncio
class TestCheckConnection:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/workspaces/check-connection")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.post("/workspaces/check-connection")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_db_connection_error(
        self, test_client_admin: httpx.AsyncClient, workspace_db_mock: MagicMock
    ):
        workspace_db_mock.check_connection.return_value = (False, "An error occured")

        response = await test_client_admin.post(
            "/workspaces/check-connection",
            json={
                "database_type": "POSTGRESQL",
                "database_host": "db.bretagne.duchy",
                "database_port": 5432,
                "database_username": "anne",
                "database_password": "hermine",
                "database_name": "fief",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == "An error occured"

    @pytest.mark.authenticated_admin(mode="session")
    async def test_success(
        self, test_client_admin: httpx.AsyncClient, workspace_db_mock: MagicMock
    ):
        workspace_db_mock.check_connection.return_value = (True, None)

        response = await test_client_admin.post(
            "/workspaces/check-connection",
            json={
                "database_type": "POSTGRESQL",
                "database_host": "db.bretagne.duchy",
                "database_port": 5432,
                "database_username": "anne",
                "database_password": "hermine",
                "database_name": "fief",
            },
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestCreateWorkspace:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/workspaces/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="api_key")
    async def test_unauthorized_with_api_key(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.post("/workspaces/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_db_connection_error(
        self, test_client_admin: httpx.AsyncClient, workspace_creation_mock: MagicMock
    ):
        workspace_creation_mock.create.side_effect = WorkspaceDatabaseConnectionError(
            "An error occured"
        )

        response = await test_client_admin.post(
            "/workspaces/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == "An error occured"

    @pytest.mark.authenticated_admin(mode="session")
    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        workspace_creation_mock: MagicMock,
        workspace: Workspace,
        workspace_admin_user: UserDB,
    ):
        workspace_creation_mock.create.side_effect = AsyncMock(return_value=workspace)

        response = await test_client_admin.post(
            "/workspaces/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json

        workspace_creation_mock.create.assert_called_once()
        create_call_args = workspace_creation_mock.create.call_args
        create_call_args[1]["user_id"] == workspace_admin_user.id
