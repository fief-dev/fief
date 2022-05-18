from typing import Optional

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from tests.data import TestData
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.parametrize("method", ["GET", "POST"])
class TestUserUserinfo:
    @pytest.mark.parametrize(
        "authorization",
        [
            None,
            "INVALID_FORMAT",
            "INVALID_SCHEMA INVALID_TOKEN",
            "Bearer INVALID_TOKEN",
        ],
    )
    async def test_unauthorized(
        self,
        method: str,
        authorization: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.request(
            method, f"{tenant_params.path_prefix}/api/userinfo", headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized(
        self,
        method: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.request(
            method, f"{tenant_params.path_prefix}/api/userinfo"
        )

        assert response.status_code == status.HTTP_200_OK

        user = tenant_params.user

        json = response.json()
        assert json == user.get_claims()


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserUpdateProfile:
    @pytest.mark.parametrize(
        "authorization",
        [
            None,
            "INVALID_FORMAT",
            "INVALID_SCHEMA INVALID_TOKEN",
            "Bearer INVALID_TOKEN",
        ],
    )
    async def test_unauthorized(
        self,
        authorization: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/profile", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized_invalid_password(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/profile", json={"password": "h"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_INVALID_PASSWORD

    @pytest.mark.access_token(user="regular")
    async def test_authorized_existing_email_address(
        self, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            "/api/profile", json={"email": "isabeau@bretagne.duchy"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized_user_fields(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/profile",
            json={
                "fields": {
                    "given_name": "Isabeau",
                    "gender": "F",
                    "onboarding_done": True,
                }
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["given_name"] == "Isabeau"
        assert json["gender"] == "F"
        assert json["onboarding_done"] is False  # Non-updatable field
