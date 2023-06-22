from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.models import Workspace
from fief.repositories import EmailVerificationRepository, UserRepository
from fief.services.acr import ACR
from tests.data import TestData, email_verification_codes
from tests.helpers import email_verification_requested_assertions
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
        authorization: str | None,
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
        authorization: str | None,
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
    async def test_invalid_json_payload(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/profile", content='{"foo": "bar",}'
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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

        assert "fields" in json
        assert json["fields"]["given_name"] == "Isabeau"
        assert json["fields"]["gender"] == "F"
        assert json["fields"]["onboarding_done"] is False  # Non-updatable field


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserChangePassword:
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
        authorization: str | None,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/password", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/password",
            json={"password": "newherminetincture"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ONE)
    async def test_invalid_password(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/password", json={"password": "h"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_INVALID_PASSWORD

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ONE)
    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/password",
            json={"password": "newherminetincture"},
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserChangeEmail:
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
        authorization: str | None,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/email/change", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.patch(
            f"{tenant_params.path_prefix}/api/email/change",
            json={"email": "anne+updated@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_existing_email_address(
        self, test_data: TestData, test_client_auth: httpx.AsyncClient
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.patch(
            f"{path_prefix}/api/email/change",
            json={"email": "isabeau@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_valid(
        self,
        test_data: TestData,
        test_client_auth: httpx.AsyncClient,
        workspace: Workspace,
        send_task_mock: MagicMock,
        workspace_session: AsyncSession,
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.patch(
            f"{path_prefix}/api/email/change",
            json={"email": "anne+updated@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        await email_verification_requested_assertions(
            email="anne+updated@bretagne.duchy",
            workspace=workspace,
            send_task_mock=send_task_mock,
            session=workspace_session,
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUserVerifyEmail:
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
        authorization: str | None,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/email/verify", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/api/email/verify",
            json={"code": "ABCDEF"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_invalid_code(
        self, test_data: TestData, test_client_auth: httpx.AsyncClient
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.post(
            f"{path_prefix}/api/email/verify",
            json={"code": "ABCDEF"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert (
            json["detail"] == APIErrorCode.USER_UPDATE_INVALID_EMAIL_VERIFICATION_CODE
        )

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_valid(
        self,
        test_data: TestData,
        test_client_auth: httpx.AsyncClient,
        workspace_session: AsyncSession,
    ):
        user = test_data["users"]["regular"]
        code = email_verification_codes["regular_update_email"][0]
        email_verification = test_data["email_verifications"]["regular_update_email"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.post(
            f"{path_prefix}/api/email/verify",
            json={"code": code},
        )

        assert response.status_code == status.HTTP_200_OK

        email_verification_repository = EmailVerificationRepository(workspace_session)
        deleted_email_verification = await email_verification_repository.get_by_id(
            email_verification.id
        )
        assert deleted_email_verification is None

        user_repository = UserRepository(workspace_session)
        updated_user = await user_repository.get_by_id(user.id)
        assert updated_user is not None
        assert updated_user.email == email_verification.email
        assert updated_user.email_verified is True
