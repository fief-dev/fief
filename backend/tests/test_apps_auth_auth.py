from typing import Dict

import httpx
import pytest
from fastapi import status
from fastapi_users.router.common import ErrorCode as FastAPIUsersErrorCode
from furl import furl

from fief.errors import ErrorCode
from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthAuthorize:
    async def test_missing_parameters(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/authorize")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unknown_client_id(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize",
            params={
                "response_type": "code",
                "client_id": "UNKNOWN",
                "scope": "openid",
                "redirect_uri": "https://bretagne.duchy/callback",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == ErrorCode.AUTH_INVALID_CLIENT_ID

    async def test_valid_client_id(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        client = tenant_params.client
        tenant = tenant_params.tenant

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize",
            params={
                "response_type": "code",
                "client_id": client.client_id,
                "scope": "openid",
                "redirect_uri": "https://bretagne.duchy/callback",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["parameters"] == {
            "response_type": "code",
            "client_id": client.client_id,
            "redirect_uri": "https://bretagne.duchy/callback",
            "scope": ["openid"],
            "state": None,
        }
        assert json["tenant"]["id"] == str(tenant.id)


@pytest.mark.asyncio
@pytest.mark.account_host
class TestAuthLogin:
    async def test_missing_parameters(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.post(f"{tenant_params.path_prefix}/login")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_bad_credentials(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        client = tenant_params.client

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "scope": "openid",
                "username": "anne@bretagne.duchy",
                "password": "foo",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == FastAPIUsersErrorCode.LOGIN_BAD_CREDENTIALS

    async def test_valid_credentials(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        client = tenant_params.client
        user = tenant_params.user

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "scope": "openid",
                "state": "STATE",
                "username": user.email,
                "password": "hermine",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        assert redirect_uri.startswith("https://bretagne.duchy/callback")
        parsed_location = furl(redirect_uri)
        assert "code" in parsed_location.query.params
        assert parsed_location.query.params["state"] == "STATE"

    async def test_none_state_not_in_redirect_uri(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        client = tenant_params.client
        user = tenant_params.user

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "username": user.email,
                "password": "hermine",
                "scope": "openid",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        parsed_location = furl(redirect_uri)
        assert "state" not in parsed_location.query.params


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
        else:
            assert "refresh_token" not in json
