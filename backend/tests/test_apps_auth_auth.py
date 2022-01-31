from typing import Dict, Optional

import httpx
import pytest
from fastapi import status
from furl import furl

from fief.db import AsyncSession
from fief.managers import (
    AuthorizationCodeManager,
    LoginSessionManager,
    RefreshTokenManager,
)
from fief.settings import settings
from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthAuthorize:
    @pytest.mark.parametrize(
        "params,error",
        [
            pytest.param(
                {
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "redirect_uri": "REDIRECT_URI",
                    "scope": "openid",
                },
                "invalid_request",
                id="Missing response_type",
            ),
            pytest.param(
                {
                    "response_type": "magic_wand",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "redirect_uri": "REDIRECT_URI",
                    "scope": "openid",
                },
                "invalid_request",
                id="Invalid response_type",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "REDIRECT_URI",
                    "scope": "openid",
                },
                "invalid_request",
                id="Missing client_id",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "INVALID_CLIENT_ID",
                    "redirect_uri": "REDIRECT_URI",
                    "scope": "openid",
                },
                "invalid_client",
                id="Invalid client",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "scope": "openid",
                },
                "invalid_request",
                id="Missing redirect_uri",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_request",
                id="Missing scope",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "redirect_uri": "REDIRECT_URI",
                    "scope": "user",
                },
                "invalid_scope",
                id="Missing openid scope",
            ),
        ],
    )
    async def test_invalid_request(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        params: Dict[str, str],
        error: str,
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == error

    async def test_valid(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        account_session: AsyncSession,
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize",
            params={
                "response_type": "code",
                "client_id": "DEFAULT_TENANT_CLIENT_ID",
                "redirect_uri": "REDIRECT_URI",
                "scope": "openid",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        login_session_cookie = response.cookies[settings.login_session_cookie_name]
        login_session_manager = LoginSessionManager(account_session)
        login_session = await login_session_manager.get_by_token(login_session_cookie)
        assert login_session is not None


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthLogin:
    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
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
            f"{tenant_params.path_prefix}/login", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_bad_credentials(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"{path_prefix}/login",
            data={
                "username": "anne@bretagne.duchy",
                "password": "foo",
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "bad_credentials"

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"{path_prefix}/login",
            data={
                "username": "anne@bretagne.duchy",
                "password": "hermine",
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]

        assert redirect_uri.startswith(login_session.redirect_uri)
        parsed_location = furl(redirect_uri)
        assert "code" in parsed_location.query.params
        assert parsed_location.query.params["state"] == login_session.state


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthTokenAuthorizationCode:
    @pytest.mark.parametrize(
        "data,error",
        [
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_client",
                id="Missing client_id",
            ),
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_client",
                id="Missing client_secret",
            ),
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "INVALID_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_client",
                id="Invalid client_id/client_secret",
            ),
            pytest.param(
                {
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_request",
                id="Missing grant_type",
            ),
            pytest.param(
                {
                    "grant_type": "magic_wand",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "unsupported_grant_type",
                id="Unsupported grant_type",
            ),
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_request",
                id="Missing code",
            ),
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                },
                "invalid_request",
                id="Missing redirect_uri",
            ),
            pytest.param(
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "REDIRECT_URI",
                },
                "invalid_grant",
                id="Invalid code",
            ),
        ],
    )
    async def test_invalid_request(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        data: Dict[str, str],
        error: str,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/token", data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == error

    async def test_client_not_matching_authorization_code(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        authorization_code = test_data["authorization_codes"]["default_regular"]
        client = test_data["clients"]["secondary_tenant"]
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "code": authorization_code.code,
                "redirect_uri": authorization_code.redirect_uri,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_grant"

    async def test_redirect_uri_not_matching(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        authorization_code = test_data["authorization_codes"]["default_regular"]
        client = authorization_code.client
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "code": authorization_code.code,
                "redirect_uri": "INVALID_REDIRECT_URI",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_grant"

    @pytest.mark.parametrize(
        "authorization_code_alias", ["default_regular", "secondary_regular"]
    )
    async def test_valid(
        self,
        authorization_code_alias: str,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        account_session: AsyncSession,
    ):
        authorization_code = test_data["authorization_codes"][authorization_code_alias]
        client = authorization_code.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.post(
            f"{path_prefix}/token",
            data={
                "grant_type": "authorization_code",
                "code": authorization_code.code,
                "redirect_uri": authorization_code.redirect_uri,
                "client_id": client.client_id,
                "client_secret": client.client_secret,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert isinstance(json["access_token"], str)
        assert isinstance(json["id_token"], str)
        assert json["token_type"] == "bearer"
        assert json["expires_in"] == 3600

        authorization_code_manager = AuthorizationCodeManager(account_session)
        used_authorization_code = await authorization_code_manager.get_by_code(
            authorization_code.code
        )
        assert used_authorization_code is None

        if "offline_access" in authorization_code.scope:
            assert json["refresh_token"] is not None
        else:
            assert "refresh_token" not in json


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthTokenRefreshToken:
    @pytest.mark.parametrize(
        "data,error",
        [
            pytest.param(
                {
                    "grant_type": "refresh_token",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Missing client_id",
            ),
            pytest.param(
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Missing client_secret",
            ),
            pytest.param(
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "INVALID_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Invalid client_id/client_secret",
            ),
            pytest.param(
                {
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_request",
                id="Missing grant_type",
            ),
            pytest.param(
                {
                    "grant_type": "magic_wand",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "unsupported_grant_type",
                id="Unsupported grant_type",
            ),
            pytest.param(
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                },
                "invalid_request",
                id="Missing refresh_token",
            ),
            pytest.param(
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_grant",
                id="Invalid code",
            ),
        ],
    )
    async def test_invalid_request(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        data: Dict[str, str],
        error: str,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/token", data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == error

    async def test_client_not_matching_refresh_token(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = test_data["clients"]["secondary_tenant"]
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "refresh_token": refresh_token.token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_grant"

    async def test_extra_scope(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = refresh_token.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.post(
            f"{path_prefix}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "refresh_token": refresh_token.token,
                "scope": "openid offline_access user",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_scope"

    async def test_valid(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        account_session: AsyncSession,
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = refresh_token.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.post(
            f"{path_prefix}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "refresh_token": refresh_token.token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert isinstance(json["access_token"], str)
        assert isinstance(json["id_token"], str)
        assert json["token_type"] == "bearer"
        assert json["expires_in"] == 3600

        if "offline_access" in refresh_token.scope:
            assert json["refresh_token"] is not None

            assert json["refresh_token"] != refresh_token.token
            refresh_token_manager = RefreshTokenManager(account_session)
            old_refresh_token = await refresh_token_manager.get_by_token(
                refresh_token.token
            )
            assert old_refresh_token is None
        else:
            assert "refresh_token" not in json
