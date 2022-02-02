from typing import Dict, Optional

import httpx
import pytest
from fastapi import status
from furl import furl

from fief.db import AsyncSession
from fief.managers import LoginSessionManager, SessionTokenManager
from fief.settings import settings
from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestGetRegister:
    @pytest.mark.parametrize("cookie", [None, "INVALID_LOGIN_SESSION"])
    async def test_invalid_login_session(
        self,
        cookie: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        cookies = {}
        if cookie is not None:
            cookies[settings.login_session_cookie_name] = cookie

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            f"{path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.account_host
class TestPostRegister:
    @pytest.mark.parametrize("cookie", [None, "INVALID_LOGIN_SESSION"])
    async def test_invalid_login_session(
        self,
        cookie: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        cookies = {}
        if cookie is not None:
            cookies[settings.login_session_cookie_name] = cookie

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email and password"),
            pytest.param({"email": "anne@bretagne.duchy"}, id="Missing password"),
            pytest.param({"password": "hermine1"}, id="Missing email"),
            pytest.param({"email": "anne", "password": "hermine1"}, id="Invalid email"),
            pytest.param(
                {"email": "anne@bretagne.duchy", "password": "h"}, id="Invalid password"
            ),
        ],
    )
    async def test_invalid_form(
        self,
        data: Dict[str, str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        login_session = tenant_params.login_session
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/register", data=data, cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_user(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "REGISTER_USER_ALREADY_EXISTS"

    async def test_new_user(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        account_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/register",
            data={"email": "louis@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]

        assert redirect_uri.startswith(login_session.redirect_uri)
        parsed_location = furl(redirect_uri)
        assert "code" in parsed_location.query.params
        assert parsed_location.query.params["state"] == login_session.state

        set_cookie_header = response.headers["Set-Cookie"]
        assert set_cookie_header.startswith(f'{settings.login_session_cookie_name}=""')
        assert "Max-Age=0" in set_cookie_header

        login_session_manager = LoginSessionManager(account_session)
        used_login_session = await login_session_manager.get_by_token(
            login_session.token
        )
        assert used_login_session is None

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_manager = SessionTokenManager(account_session)
        session_token = await session_token_manager.get_by_token(session_cookie)
        assert session_token is not None

    async def test_no_email_conflict_on_another_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["secondary"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND
