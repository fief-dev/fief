from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.managers.session_token import SessionTokenManager
from fief.models import session_token
from fief.settings import settings
from tests.data import TestData


@pytest.mark.asyncio
class TestAuthLogin:
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


@pytest.mark.asyncio
class TestAuthCallback:
    async def test_missing_code(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/auth/callback")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        fief_client_mock: MagicMock,
        global_session: AsyncSession,
    ):
        fief_client_mock.auth_callback.side_effect = AsyncMock(
            return_value=(
                {"access_token": "ACCESS_TOKEN", "id_token": "ID_TOKEN"},
                {"email": "anne@bretagne.duchy"},
            )
        )

        response = await test_client_admin.get(
            "/auth/callback", params={"code": "CODE"}
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies.get(settings.fief_admin_session_cookie_name)
        assert session_cookie is not None

        session_token_manager = SessionTokenManager(global_session)
        session_token = await session_token_manager.get_by_token(session_cookie)
        assert session_token is not None
        assert session_token.userinfo == {"email": "anne@bretagne.duchy"}


@pytest.mark.session_token(user="regular")
async def test_auth_user(test_client_admin: httpx.AsyncClient, test_data: TestData):
    response = await test_client_admin.get("/auth/user")

    assert response.status_code == status.HTTP_200_OK

    user = test_data["users"]["regular"]

    json = response.json()
    assert json["sub"] == str(user.id)
    assert json["email"] == user.email
