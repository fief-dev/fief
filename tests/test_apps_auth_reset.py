from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status
from jwcrypto import jwt

from fief.crypto.password import password_helper
from fief.models import User
from fief.services.user_manager import RESET_PASSWORD_TOKEN_AUDIENCE
from fief.settings import settings
from fief.tasks import on_after_forgot_password
from tests.data import TestData
from tests.helpers import str_match
from tests.types import TenantParams


def generate_jwt(user: User) -> str:
    claims = {
        "sub": str(user.id),
        "password_fgpt": password_helper.hash(user.hashed_password),
        "aud": RESET_PASSWORD_TOKEN_AUDIENCE,
    }
    signing_key = user.tenant.get_sign_jwk()
    token = jwt.JWT(header={"alg": "RS256", "kid": signing_key["kid"]}, claims=claims)
    token.make_signed_token(signing_key)

    return token.serialize()


@pytest.mark.asyncio
class TestGetForgotPassword:
    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/forgot")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestPostForgotPassword:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email"),
            pytest.param({"email": "anne"}, id="Invalid email"),
        ],
    )
    async def test_invalid_form(
        self,
        data: dict[str, str],
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/forgot",
            data={**data, "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_not_existing_user(
        self,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        send_task_mock: MagicMock,
    ):
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/forgot",
            data={"email": "louis@bretagne.duchy", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_200_OK

        send_task_mock.assert_not_called()

    async def test_existing_user(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        user = test_data["users"]["regular"]

        response = await test_client_auth_csrf.post(
            "/forgot", data={"email": "anne@bretagne.duchy", "csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_200_OK

        send_task_mock.assert_called_with(
            on_after_forgot_password,
            str(user.id),
            str_match(r"/reset.*token="),
        )


@pytest.mark.asyncio
class TestGetResetPassword:
    async def test_missing_token(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/reset")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "missing_token"

    async def test_valid(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/reset", params={"token": "TOKEN"}
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestPostResetPassword:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing password and token"),
            pytest.param({"password": "newherminetincture"}, id="Missing token"),
            pytest.param({"token": "TOKEN"}, id="Missing password"),
            pytest.param(
                {"token": "TOKEN", "password": "newherminetincture"}, id="Invalid token"
            ),
        ],
    )
    async def test_invalid_form(
        self,
        data: dict[str, str],
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/reset",
            data={**data, "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_invalid_password(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        token = generate_jwt(user)

        response = await test_client_auth_csrf.post(
            "/reset", data={"password": "h", "token": token, "csrf_token": csrf_token}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_valid(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        token = generate_jwt(user)

        response = await test_client_auth_csrf.post(
            "/reset",
            data={
                "password": "newherminetincture",
                "token": token,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_valid_with_login_session(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        token = generate_jwt(user)
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth_csrf.post(
            "/reset",
            data={
                "password": "newherminetincture",
                "token": token,
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/login")
