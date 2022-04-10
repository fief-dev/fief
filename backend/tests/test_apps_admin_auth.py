from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.managers import AdminSessionTokenManager
from fief.models import AdminSessionToken
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
        assert location == "http://localhost/authorize"

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
        session_token_hash = get_token_hash(session_cookie)
        session_token = await admin_session_token_manager.get_by_token(
            session_token_hash
        )
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


@pytest.mark.asyncio
class TestAuthLogout:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self,
        test_client_admin: httpx.AsyncClient,
        admin_session_token: Tuple[AdminSessionToken, str],
        main_session: AsyncSession,
        fief_client_mock: MagicMock,
    ):
        fief_client_mock.base_url = "https://bretagne.fief.dev"
        response = await test_client_admin.get("/auth/logout")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert (
            location
            == "https://bretagne.fief.dev/logout?redirect_uri=http://api.fief.dev/admin/"
        )

        assert "Set-Cookie" in response.headers

        admin_session_token_manager = AdminSessionTokenManager(main_session)
        deleted_admin_session_token = await admin_session_token_manager.get_by_id(
            admin_session_token[0].id
        )
        assert deleted_admin_session_token is None
