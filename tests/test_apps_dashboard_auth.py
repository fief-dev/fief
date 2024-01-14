from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status
from fief_client import FiefAccessTokenMissingPermission

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.repositories import AdminSessionTokenRepository
from fief.settings import settings
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestAuthLogin:
    async def test_success(
        self,
        test_client_dashboard: httpx.AsyncClient,
        fief_client_mock: MagicMock,
    ):
        fief_client_mock.auth_url.side_effect = AsyncMock(
            return_value="http://localhost/authorize"
        )

        response = await test_client_dashboard.get("/auth/login")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == "http://localhost/authorize"

        fief_client_mock.auth_url.assert_called_once_with(
            redirect_uri="http://api.fief.dev/auth/callback",
            scope=["openid"],
            extras_params={"screen": "login"},
        )


@pytest.mark.asyncio
class TestAuthCallback:
    async def test_missing_code(self, test_client_dashboard: httpx.AsyncClient):
        response = await test_client_dashboard.get("/auth/callback")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_permission(
        self, test_client_dashboard: httpx.AsyncClient, fief_client_mock: MagicMock
    ):
        fief_client_mock.auth_callback.side_effect = AsyncMock(
            return_value=(
                {"access_token": "ACCESS_TOKEN", "id_token": "ID_TOKEN"},
                {"email": "anne@bretagne.duchy"},
            )
        )
        fief_client_mock.validate_access_token.side_effect = (
            FiefAccessTokenMissingPermission()
        )

        response = await test_client_dashboard.get(
            "/auth/callback", params={"code": "CODE"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        session_cookie = response.cookies.get(settings.fief_admin_session_cookie_name)
        assert session_cookie is None

    async def test_success(
        self,
        test_client_dashboard: httpx.AsyncClient,
        fief_client_mock: MagicMock,
        main_session: AsyncSession,
    ):
        fief_client_mock.auth_callback.side_effect = AsyncMock(
            return_value=(
                {"access_token": "ACCESS_TOKEN", "id_token": "ID_TOKEN"},
                {"email": "anne@bretagne.duchy"},
            )
        )

        response = await test_client_dashboard.get(
            "/auth/callback", params={"code": "CODE"}
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies.get(settings.fief_admin_session_cookie_name)
        assert session_cookie is not None

        admin_session_token_repository = AdminSessionTokenRepository(main_session)
        session_token_hash = get_token_hash(session_cookie)
        session_token = await admin_session_token_repository.get_by_token(
            session_token_hash
        )
        assert session_token is not None
        assert session_token.userinfo == {"email": "anne@bretagne.duchy"}


@pytest.mark.asyncio
class TestAuthProfile:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/auth/profile")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(self, test_client_dashboard: httpx.AsyncClient):
        response = await test_client_dashboard.get("/auth/profile")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == f"//{settings.fief_domain}"


@pytest.mark.asyncio
class TestAuthLogout:
    async def test_unauthorized(self, test_client_dashboard: httpx.AsyncClient):
        response = await test_client_dashboard.get("/auth/logout")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        main_session: AsyncSession,
        fief_client_mock: MagicMock,
    ):
        token = test_client_dashboard.cookies.get(
            settings.fief_admin_session_cookie_name
        )
        assert token is not None
        token_hash = get_token_hash(token)

        fief_client_mock.base_url = "https://bretagne.fief.dev"
        response = await test_client_dashboard.get("/auth/logout")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert (
            location
            == f"//{settings.fief_domain}/logout?redirect_uri=http://api.fief.dev/admin/"
        )

        assert "Set-Cookie" in response.headers

        admin_session_token_repository = AdminSessionTokenRepository(main_session)
        deleted_admin_session_token = await admin_session_token_repository.get_by_token(
            token_hash
        )
        assert deleted_admin_session_token is None
