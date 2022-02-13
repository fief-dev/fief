from typing import Dict
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.models import Account
from fief.settings import settings
from fief.tasks import on_after_forgot_password
from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestGetForgotPassword:
    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/forgot")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.account_host
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
        account: Account,
        account_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        user = test_data["users"]["regular"]
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/forgot", data={"email": "anne@bretagne.duchy"}
        )

        assert response.status_code == status.HTTP_200_OK

        send_task_mock.assert_called_once()
        send_task_call_args = send_task_mock.call_args[0]
        assert send_task_call_args[0] == on_after_forgot_password
        assert send_task_call_args[1] == str(user.id)
        assert send_task_call_args[2] == str(account.id)
        assert "/reset" in send_task_call_args[3]
        assert "token=" in send_task_call_args[3]
