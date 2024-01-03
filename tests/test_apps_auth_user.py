from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio
from fastapi import status

from fief.crypto.access_token import generate_access_token
from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.repositories import EmailVerificationRepository, UserRepository
from fief.services.acr import ACR
from tests.data import TestData, email_verification_codes
from tests.helpers import email_verification_requested_assertions
from tests.types import TenantParams


@pytest.fixture
def access_token(
    request: pytest.FixtureRequest, test_data: TestData, tenant_params: TenantParams
) -> Callable[[httpx.AsyncClient], httpx.AsyncClient]:
    def _access_token(http_client: httpx.AsyncClient) -> httpx.AsyncClient:
        marker = request.node.get_closest_marker("access_token")
        if marker:
            from_tenant_params: bool = marker.kwargs.get("from_tenant_params", False)
            if from_tenant_params:
                user = tenant_params.user
            else:
                user_alias = marker.kwargs["user"]
                user = test_data["users"][user_alias]

            acr: ACR = marker.kwargs.get("acr", ACR.LEVEL_ZERO)

            user_tenant = user.tenant
            client = next(
                client
                for _, client in test_data["clients"].items()
                if client.tenant_id == user_tenant.id
            )

            user_permissions = [
                permission.permission.codename
                for permission in test_data["user_permissions"].values()
            ]

            access_token = generate_access_token(
                user_tenant.get_sign_jwk(),
                user_tenant.get_host(),
                client,
                datetime.now(UTC),
                acr,
                user,
                ["openid"],
                user_permissions,
                3600,
            )
            http_client.headers["Authorization"] = f"Bearer {access_token}"
        print("hTTP client", http_client)
        return http_client

    return _access_token


@pytest_asyncio.fixture
async def test_client_auth_access_token(
    test_client_auth: httpx.AsyncClient,
    access_token: Callable[[httpx.AsyncClient], httpx.AsyncClient],
) -> AsyncGenerator[httpx.AsyncClient, None]:
    test_client_auth_access_token = access_token(test_client_auth)
    yield test_client_auth_access_token


@pytest.mark.asyncio
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
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth_access_token.request(
            method, f"{tenant_params.path_prefix}/api/userinfo", headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized(
        self,
        method: str,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.request(
            method, f"{tenant_params.path_prefix}/api/userinfo"
        )

        assert response.status_code == status.HTTP_200_OK

        user = tenant_params.user

        json = response.json()
        assert json == user.get_claims()


@pytest.mark.asyncio
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
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/profile", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_invalid_json_payload(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/profile", content='{"foo": "bar",}'
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized_user_fields(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
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
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/password", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/password",
            json={"password": "newherminetincture"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ONE)
    async def test_invalid_password(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/password", json={"password": "h"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_INVALID_PASSWORD

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ONE)
    async def test_valid(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/password",
            json={"password": "newherminetincture"},
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
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
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/email/change", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.patch(
            f"{tenant_params.path_prefix}/api/email/change",
            json={"email": "anne+updated@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_existing_email_address(
        self, test_data: TestData, test_client_auth_access_token: httpx.AsyncClient
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth_access_token.patch(
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
        test_client_auth_access_token: httpx.AsyncClient,
        send_task_mock: MagicMock,
        main_session: AsyncSession,
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth_access_token.patch(
            f"{path_prefix}/api/email/change",
            json={"email": "anne+updated@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        await email_verification_requested_assertions(
            user=user,
            email="anne+updated@bretagne.duchy",
            send_task_mock=send_task_mock,
            session=main_session,
        )


@pytest.mark.asyncio
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
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth_access_token.post(
            f"{tenant_params.path_prefix}/api/email/verify", headers=headers, json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True, acr=ACR.LEVEL_ZERO)
    async def test_acr_too_low(
        self,
        tenant_params: TenantParams,
        test_client_auth_access_token: httpx.AsyncClient,
    ):
        response = await test_client_auth_access_token.post(
            f"{tenant_params.path_prefix}/api/email/verify",
            json={"code": "ABCDEF"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        json = response.json()
        assert json["detail"] == APIErrorCode.ACR_TOO_LOW

    @pytest.mark.access_token(user="regular", acr=ACR.LEVEL_ONE)
    async def test_invalid_code(
        self, test_data: TestData, test_client_auth_access_token: httpx.AsyncClient
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth_access_token.post(
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
        test_client_auth_access_token: httpx.AsyncClient,
        main_session: AsyncSession,
    ):
        user = test_data["users"]["regular"]
        code = email_verification_codes["regular_update_email"][0]
        email_verification = test_data["email_verifications"]["regular_update_email"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth_access_token.post(
            f"{path_prefix}/api/email/verify",
            json={"code": code},
        )

        assert response.status_code == status.HTTP_200_OK

        email_verification_repository = EmailVerificationRepository(main_session)
        deleted_email_verification = await email_verification_repository.get_by_id(
            email_verification.id
        )
        assert deleted_email_verification is None

        user_repository = UserRepository(main_session)
        updated_user = await user_repository.get_by_id(user.id)
        assert updated_user is not None
        assert updated_user.email == email_verification.email
        assert updated_user.email_verified is True
