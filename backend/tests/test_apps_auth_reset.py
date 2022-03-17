from typing import Dict
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status
from fastapi_users.jwt import generate_jwt

from fief.db import AsyncSession
from fief.dependencies.users import UserManager
from fief.models import Workspace
from fief.settings import settings
from fief.tasks import on_after_forgot_password
from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetForgotPassword:
    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/forgot")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestPostForgotPassword:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email"),
            pytest.param({"email": "anne"}, id="Invalid email"),
        ],
    )
    async def test_invalid_form(
        self,
        data: Dict[str, str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/forgot", data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_not_existing_user(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        send_task_mock: MagicMock,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/forgot",
            data={"email": "louis@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_200_OK

        send_task_mock.assert_not_called()

    async def test_existing_user(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        send_task_mock: MagicMock,
    ):
        user = test_data["users"]["regular"]

        response = await test_client_auth.post(
            "/forgot", data={"email": "anne@bretagne.duchy"}
        )

        assert response.status_code == status.HTTP_200_OK

        send_task_mock.assert_called_once()
        send_task_call_args = send_task_mock.call_args[0]
        assert send_task_call_args[0] == on_after_forgot_password
        assert send_task_call_args[1] == str(user.id)
        assert send_task_call_args[2] == str(workspace.id)
        assert "/reset" in send_task_call_args[3]
        assert "token=" in send_task_call_args[3]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetResetPassword:
    async def test_missing_token(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/reset")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "missing_token"

    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/reset", params={"token": "TOKEN"}
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestPostResetPassword:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing password and token"),
            pytest.param({"password": "hermine1"}, id="Missing token"),
            pytest.param({"token": "TOKEN"}, id="Missing password"),
            pytest.param(
                {"token": "TOKEN", "password": "hermine1"}, id="Invalid token"
            ),
        ],
    )
    async def test_invalid_form(
        self,
        data: Dict[str, str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/reset", data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_invalid_password(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        token_data = {
            "user_id": str(user.id),
            "aud": UserManager.reset_password_token_audience,
        }
        token = generate_jwt(token_data, UserManager.reset_password_token_secret, 3600)

        response = await test_client_auth.post(
            "/reset", data={"password": "h", "token": token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_password"

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        token_data = {
            "user_id": str(user.id),
            "aud": UserManager.reset_password_token_audience,
        }
        token = generate_jwt(token_data, UserManager.reset_password_token_secret, 3600)

        response = await test_client_auth.post(
            "/reset", data={"password": "hermine1", "token": token}
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_valid_with_login_session(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        token_data = {
            "user_id": str(user.id),
            "aud": UserManager.reset_password_token_audience,
        }
        token = generate_jwt(token_data, UserManager.reset_password_token_secret, 3600)
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/reset", data={"password": "hermine1", "token": token}, cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/login")
