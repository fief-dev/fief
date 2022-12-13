import json
from base64 import b64encode
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import itsdangerous
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db.types import SSL_MODES, DatabaseType, PostreSQLSSLMode
from fief.models import User, Workspace
from fief.services.workspace_db import WorkspaceDatabaseConnectionError
from fief.settings import settings
from tests.helpers import admin_dashboard_unauthorized_assertions

EncodeSessionData = Callable[[dict[str, Any]], str]


@pytest.fixture
def encode_session_data() -> EncodeSessionData:
    def _encode_session_data(data: dict[str, Any]) -> str:
        signer = itsdangerous.TimestampSigner(str(settings.secret.get_secret_value()))
        encoded_data = b64encode(json.dumps(data).encode("utf-8"))
        return signer.sign(encoded_data).decode("utf-8")

    return _encode_session_data


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspace:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/workspaces/create")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_redirect_to_step1(
        self, test_client_admin_dashboard: httpx.AsyncClient
    ):
        response = await test_client_admin_dashboard.get("/workspaces/create")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"].endswith("/workspaces/create/step1")


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspaceStep1:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/workspaces/create/step1")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step1", data={"csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step1",
            data={"name": "Burgundy", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.cookies.get(settings.session_data_cookie_name) is not None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspaceStep2:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/workspaces/create/step2")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step2",
            data={
                "database": "INVALID_CHOICE",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "choice,redirection",
        (
            [
                ("cloud", "/workspaces/create/step4"),
                ("custom", "/workspaces/create/step3"),
            ]
        ),
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self,
        choice: str,
        redirection: str,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step2",
            data={"database": choice, "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["Location"].endswith(redirection)


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspaceStep3:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/workspaces/create/step3")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_prefill_from_database_type(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "csrf_token": csrf_token,
            },
            headers={"HX-Trigger": "database_type"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        ssl_mode_options = html.find("select", id="database_ssl_mode").find_all(
            "option"
        )
        assert len(ssl_mode_options) == len(SSL_MODES[DatabaseType.POSTGRESQL])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "database_host": "db.bretagne.duchy",
                "database_port": 5432,
                "database_username": "anne",
                "database_password": "hermine",
                "database_name": "fief",
                "database_ssl_mode": PostreSQLSSLMode.ALLOW.value,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["Location"].endswith("/workspaces/create/step4")


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspaceStep3CheckConnection:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3/check-connection", data={}
        )

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3/check-connection",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_db_connection_error(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_db_mock: MagicMock,
    ):
        workspace_db_mock.check_connection.return_value = (False, "An error occured")

        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3/check-connection",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "database_host": "db.bretagne.duchy",
                "database_port": 5432,
                "database_username": "anne",
                "database_password": "hermine",
                "database_name": "fief",
                "database_ssl_mode": PostreSQLSSLMode.ALLOW.value,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        html = BeautifulSoup(response.text, features="html.parser")
        assert "An error occured" in html.text

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_success(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_db_mock: MagicMock,
    ):
        workspace_db_mock.check_connection.return_value = (True, None)

        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step3/check-connection",
            data={
                "database_type": DatabaseType.POSTGRESQL.value,
                "database_host": "db.bretagne.duchy",
                "database_port": 5432,
                "database_username": "anne",
                "database_password": "hermine",
                "database_name": "fief",
                "database_ssl_mode": PostreSQLSSLMode.ALLOW.value,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        assert "Successfully connected to the database" in html.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateWorkspaceStep4:
    async def test_unauthorized(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/workspaces/create/step4")

        admin_dashboard_unauthorized_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_missing_data_session(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step4", data={"csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["Location"].endswith("/workspaces/create")

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_invalid_data_session(
        self,
        encode_session_data: EncodeSessionData,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):

        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step4",
            data={"csrf_token": csrf_token},
            cookies={
                settings.session_data_cookie_name: encode_session_data(
                    {
                        "create_workspace": {
                            "database_type": DatabaseType.POSTGRESQL.value
                        }
                    }
                )
            },
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["Location"].endswith("/workspaces/create")

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_db_connection_error(
        self,
        encode_session_data: EncodeSessionData,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_creation_mock: MagicMock,
    ):
        workspace_creation_mock.create.side_effect = WorkspaceDatabaseConnectionError(
            "An error occured"
        )

        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step4",
            data={
                "csrf_token": csrf_token,
            },
            cookies={
                settings.session_data_cookie_name: encode_session_data(
                    {
                        "create_workspace": {
                            "name": "Burgundy",
                            "database_type": DatabaseType.POSTGRESQL.value,
                            "database_host": "db.bretagne.duchy",
                            "database_port": 5432,
                            "database_username": "anne",
                            "database_password": "hermine",
                            "database_name": "fief",
                            "database_ssl_mode": PostreSQLSSLMode.ALLOW.value,
                        }
                    }
                )
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        html = BeautifulSoup(response.text, features="html.parser")
        assert "An error occured" in html.text

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_success(
        self,
        encode_session_data: EncodeSessionData,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_creation_mock: MagicMock,
        workspace: Workspace,
        workspace_admin_user: User,
    ):
        workspace_creation_mock.create.side_effect = AsyncMock(return_value=workspace)

        response = await test_client_admin_dashboard.post(
            "/workspaces/create/step4",
            data={
                "csrf_token": csrf_token,
            },
            cookies={
                settings.session_data_cookie_name: encode_session_data(
                    {
                        "create_workspace": {
                            "name": "Burgundy",
                            "database_type": DatabaseType.POSTGRESQL.value,
                            "database_host": "db.bretagne.duchy",
                            "database_port": 5432,
                            "database_username": "anne",
                            "database_password": "hermine",
                            "database_name": "fief",
                            "database_ssl_mode": PostreSQLSSLMode.ALLOW.value,
                        }
                    }
                )
            },
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["Location"] == f"http://{workspace.domain}/admin/"

        workspace_creation_mock.create.assert_called_once()
        create_call_args = workspace_creation_mock.create.call_args
        create_call_args[1]["user_id"] == workspace_admin_user.id
