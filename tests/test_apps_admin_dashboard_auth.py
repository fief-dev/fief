from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.models import AdminSessionToken
from fief.repositories import AdminSessionTokenRepository
from fief.settings import settings
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthLogin:
    async def test_success(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        fief_client_mock: MagicMock,
    ):
        fief_client_mock.auth_url.side_effect = AsyncMock(
            return_value="http://localhost/authorize"
        )

        response = await test_client_admin_dashboard.get("/auth/login")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == "http://localhost/authorize"

        fief_client_mock.auth_url.assert_called_once_with(
            redirect_uri="http://bretagne.localhost:8000/auth/callback",
            scope=["openid"],
            extras_params={"screen": "login"},
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthCallback:
    async def test_missing_code(self, test_client_admin_dashboard: httpx.AsyncClient):
        response = await test_client_admin_dashboard.get("/auth/callback")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_success(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        fief_client_mock: MagicMock,
        main_session: AsyncSession,
    ):
        fief_client_mock.auth_callback.side_effect = AsyncMock(
            return_value=(
                {"access_token": "ACCESS_TOKEN", "id_token": "ID_TOKEN"},
                {"email": "anne@bretagne.duchy"},
            )
        )

        response = await test_client_admin_dashboard.get(
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
@pytest.mark.workspace_host
class TestAuthLogout:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.get("/auth/logout")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        admin_session_token: tuple[AdminSessionToken, str],
        main_session: AsyncSession,
        fief_client_mock: MagicMock,
    ):
        fief_client_mock.base_url = "https://bretagne.fief.dev"
        response = await test_client_admin_dashboard.get("/auth/logout")

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert (
            location
            == f"//{settings.fief_domain}/logout?redirect_uri=http://bretagne.localhost:8000/admin/"
        )

        assert "Set-Cookie" in response.headers

        admin_session_token_repository = AdminSessionTokenRepository(main_session)
        deleted_admin_session_token = await admin_session_token_repository.get_by_id(
            admin_session_token[0].id
        )
        assert deleted_admin_session_token is None
