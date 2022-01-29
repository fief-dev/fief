from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status


@pytest.mark.asyncio
class TestLogin:
    async def test_success(
        self, test_client_admin: httpx.AsyncClient, fief_client_mock: MagicMock
    ):
        fief_client_mock.auth_url.side_effect = AsyncMock(return_value="AUTHORIZE_URL")

        response = await test_client_admin.get("/auth/login")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == "AUTHORIZE_URL"

        fief_client_mock.auth_url.assert_called_once_with(
            redirect_uri="http://api.fief.dev/auth/callback", scope=["openid"]
        )
