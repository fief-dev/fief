from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.errors import ErrorCode
from fief.models import Account
from fief.services.account_db import AccountDatabaseConnectionError


@pytest.mark.asyncio
class TestCreateAccount:
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
        assert json["detail"] == ErrorCode.ACCOUNT_DB_CONNECTION_ERROR

    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        account_creation_mock: MagicMock,
        account: Account,
    ):
        account_creation_mock.create.side_effect = AsyncMock(return_value=account)

        response = await test_client_admin.post(
            "/accounts/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        account_creation_mock.create.assert_called_once()

        json = response.json()
        assert "id" in json
