from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from fief.models import Account
from fief.schemas.user import UserDB
from fief.services.account_db import AccountDatabaseConnectionError


@pytest.mark.asyncio
class TestCreateAccount:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/accounts/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.admin_session_token
    async def test_db_connection_error(
        self, test_client_admin: httpx.AsyncClient, account_creation_mock: MagicMock
    ):
        account_creation_mock.create.side_effect = AccountDatabaseConnectionError()

        response = await test_client_admin.post(
            "/accounts/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.ACCOUNT_DB_CONNECTION_ERROR

    @pytest.mark.admin_session_token
    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        account_creation_mock: MagicMock,
        account: Account,
        account_admin_user: UserDB,
    ):
        account_creation_mock.create.side_effect = AsyncMock(return_value=account)

        response = await test_client_admin.post(
            "/accounts/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json

        account_creation_mock.create.assert_called_once()
        create_call_args = account_creation_mock.create.call_args
        create_call_args[1]["user_id"] == account_admin_user.id
