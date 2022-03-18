from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.managers import AdminSessionTokenManager
from fief.schemas.user import UserDB
from fief.settings import settings


@pytest.mark.asyncio
class TestAuthLogin:
    async def test_success(
        self, test_client_admin: httpx.AsyncClient, fief_client_mock: MagicMock
    ):
        fief_client_mock.auth_url.side_effect = AsyncMock(
            return_value="http://localhost/authorize"
        )

        response = await test_client_admin.get("/auth/login")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == "http://api.fief.dev/authorize"

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
        main_session: AsyncSession,
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

        admin_session_token_manager = AdminSessionTokenManager(main_session)
        session_token = await admin_session_token_manager.get_by_token(session_cookie)
        assert session_token is not None
        assert session_token.userinfo == {"email": "anne@bretagne.duchy"}


@pytest.mark.authenticated_admin(mode="session")
async def test_auth_userinfo(
    test_client_admin: httpx.AsyncClient, workspace_admin_user: UserDB
):
    response = await test_client_admin.get("/auth/userinfo")

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert json["sub"] == str(workspace_admin_user.id)
    assert json["email"] == workspace_admin_user.email
