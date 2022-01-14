import re
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.errors import ErrorCode
from fief.services.account_db import AccountDatabaseConnectionError


@pytest.mark.asyncio
@pytest.mark.test_data
class TestCreateAccount:
    async def test_db_connection_error(
        self, test_client_supervisor: httpx.AsyncClient, account_db_mock: MagicMock
    ):
        account_db_mock.migrate.side_effect = AccountDatabaseConnectionError()

        response = await test_client_supervisor.post(
            "/accounts/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == ErrorCode.ACCOUNT_DB_CONNECTION_ERROR

    async def test_success(
        self, test_client_supervisor: httpx.AsyncClient, account_db_mock: MagicMock
    ):
        response = await test_client_supervisor.post(
            "/accounts/",
            json={"name": "Burgundy"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        account_db_mock.migrate.assert_called_once()

        json = response.json()
        assert json["id"] is not None
        assert json["domain"] == "burgundy.fief.dev"

        assert "sign_jwk" not in json
        assert "encrypt_jwk" not in json

    async def test_avoid_domain_collision(
        self, test_client_supervisor: httpx.AsyncClient, account_db_mock: MagicMock
    ):
        response = await test_client_supervisor.post(
            "/accounts/",
            json={"name": "Bretagne"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        account_db_mock.migrate.assert_called_once()

        json = response.json()
        assert json["id"] is not None
        assert re.match(r"bretagne-\w+\.fief\.dev", json["domain"])

        assert "sign_jwk" not in json
        assert "encrypt_jwk" not in json
