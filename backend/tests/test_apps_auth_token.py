import base64
from typing import Dict, Tuple

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.managers import AuthorizationCodeManager, RefreshTokenManager
from fief.models import Client
from tests.conftest import TenantParams
from tests.data import TestData

AUTH_METHODS = ["client_secret_basic", "client_secret_post"]


def get_basic_authorization_header(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"


def get_authenticated_request_headers_data(
    method: str, client: Client
) -> Tuple[Dict[str, str], Dict[str, str]]:
    headers: Dict[str, str] = {}
    data: Dict[str, str] = {}
    if method == "client_secret_basic":
        headers["Authorization"] = get_basic_authorization_header(
            client.client_id, client.client_secret
        )
    elif method == "client_secret_post":
        data["client_id"] = client.client_id
        data["client_secret"] = client.client_secret
    return headers, data


@pytest.mark.workspace_host
class TestAuthTokenAuthorizationCode:
    @pytest.mark.parametrize(
        "headers,data,error",
        [
            pytest.param(
                {},
                {
                    "grant_type": "authorization_code",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_client",
                id="Missing client_id in body",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_client",
                id="Missing client_secret in body",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "INVALID_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_client",
                id="Invalid client_id/client_secret in body",
            ),
            pytest.param(
                {
                    "Authorization": get_basic_authorization_header(
                        "DEFAULT_TENANT_CLIENT_ID", "INVALID_CLIENT_SECRET"
                    )
                },
                {
                    "grant_type": "authorization_code",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_client",
                id="Invalid client_id/client_secret in authorization header",
            ),
            pytest.param(
                {},
                {
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_request",
                id="Missing grant_type",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "magic_wand",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "unsupported_grant_type",
                id="Unsupported grant_type",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_request",
                id="Missing code",
            ),
            pytest.param(
                {},
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
                {},
                {
                    "grant_type": "authorization_code",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
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
        headers: Dict[str, str],
        data: Dict[str, str],
        error: str,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/token", data=data, headers=headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == error

    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_client_not_matching_authorization_code(
        self,
        auth_method: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        authorization_code = test_data["authorization_codes"]["default_regular"]
        client = test_data["clients"]["secondary_tenant"]
        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "authorization_code",
                "code": authorization_code.code,
                "redirect_uri": authorization_code.redirect_uri,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_grant"

    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_redirect_uri_not_matching(
        self,
        auth_method: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        authorization_code = test_data["authorization_codes"]["default_regular"]
        client = authorization_code.client
        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "authorization_code",
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
    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_valid(
        self,
        auth_method: str,
        authorization_code_alias: str,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        authorization_code = test_data["authorization_codes"][authorization_code_alias]
        client = authorization_code.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "authorization_code",
                "code": authorization_code.code,
                "redirect_uri": authorization_code.redirect_uri,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert isinstance(json["access_token"], str)
        assert isinstance(json["id_token"], str)
        assert json["token_type"] == "bearer"
        assert json["expires_in"] == 3600

        authorization_code_manager = AuthorizationCodeManager(workspace_session)
        used_authorization_code = await authorization_code_manager.get_by_code(
            authorization_code.code
        )
        assert used_authorization_code is None

        if "offline_access" in authorization_code.scope:
            assert json["refresh_token"] is not None
        else:
            assert "refresh_token" not in json


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthTokenRefreshToken:
    @pytest.mark.parametrize(
        "headers,data,error",
        [
            pytest.param(
                {},
                {
                    "grant_type": "refresh_token",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Missing client_id in body",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Missing client_secret in body",
            ),
            pytest.param(
                {},
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "INVALID_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_client",
                id="Invalid client_id/client_secret in body",
            ),
            pytest.param(
                {
                    "Authorization": get_basic_authorization_header(
                        "DEFAULT_TENANT_CLIENT_ID", "INVALID_CLIENT_SECRET"
                    )
                },
                {
                    "grant_type": "authorization_code",
                    "code": "CODE",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_client",
                id="Invalid client_id/client_secret in authorization header",
            ),
            pytest.param(
                {},
                {
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                    "refresh_token": "REFRESH_TOKEN",
                },
                "invalid_request",
                id="Missing grant_type",
            ),
            pytest.param(
                {},
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
                {},
                {
                    "grant_type": "refresh_token",
                    "client_id": "DEFAULT_TENANT_CLIENT_ID",
                    "client_secret": "DEFAULT_TENANT_CLIENT_SECRET",
                },
                "invalid_request",
                id="Missing refresh_token",
            ),
            pytest.param(
                {},
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
        headers: Dict[str, str],
        data: Dict[str, str],
        error: str,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/token", data=data, headers=headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == error

    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_client_not_matching_refresh_token(
        self,
        auth_method: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = test_data["clients"]["secondary_tenant"]
        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_grant"

    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_extra_scope(
        self, auth_method: str, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = refresh_token.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.token,
                "scope": "openid offline_access user",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["error"] == "invalid_scope"

    @pytest.mark.parametrize("auth_method", AUTH_METHODS)
    async def test_valid(
        self,
        auth_method: str,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        refresh_token = test_data["refresh_tokens"]["default_regular"]
        client = refresh_token.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        headers, data = get_authenticated_request_headers_data(auth_method, client)
        response = await test_client_auth.post(
            f"{path_prefix}/api/token",
            headers=headers,
            data={
                **data,
                "grant_type": "refresh_token",
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
            refresh_token_manager = RefreshTokenManager(workspace_session)
            old_refresh_token = await refresh_token_manager.get_by_token(
                refresh_token.token
            )
            assert old_refresh_token is None
        else:
            assert "refresh_token" not in json
