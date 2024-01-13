from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import EmailVerificationRepository, UserRepository
from fief.settings import settings
from tests.data import TestData, email_verification_codes, session_token_tokens
from tests.helpers import email_verification_requested_assertions
from tests.types import TenantParams


@pytest.mark.asyncio
class TestAuthUpdateProfile:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        response = await test_client_auth_csrf.get(f"{tenant_params.path_prefix}/")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert (
            response.headers["Location"]
            == f"http://api.fief.dev{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://api.fief.dev/login"

    @pytest.mark.htmx()
    async def test_valid_get(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        inputs = html.find_all("input")
        assert len(inputs) > 0

    @pytest.mark.htmx()
    async def test_update_fields(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        session_token = session_token_tokens["regular"]
        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]

        response = await test_client_auth_csrf.post(
            "/",
            cookies=cookies,
            data={
                "fields.given_name": "Isabeau",
                "fields.gender": "F",
                "fields.onboarding_done": True,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_repository = UserRepository(main_session)
        user = await user_repository.get_by_id(test_data["users"]["regular"].id)
        assert user is not None
        assert user.fields["given_name"] == "Isabeau"
        assert user.fields["gender"] == "F"
        assert user.fields["onboarding_done"] is False  # Non-updatable field


@pytest.mark.asyncio
class TestAuthUpdatePassword:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/password"
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert (
            response.headers["Location"]
            == f"http://api.fief.dev{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/password", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://api.fief.dev/login"

    @pytest.mark.htmx()
    async def test_valid_get(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/password", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        password_inputs = html.find_all("input", {"type": "password"})
        assert len(password_inputs) == 3

    @pytest.mark.htmx()
    async def test_update_invalid_new_password(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/password",
            cookies=cookies,
            data={
                "old_password": "herminetincture",
                "new_password": "a",
                "new_password_confirm": "a",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.htmx()
    async def test_update_invalid_old_password(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/password",
            cookies=cookies,
            data={
                "old_password": "INVALID_PASSWORD",
                "new_password": "newherminetincture",
                "new_password_confirm": "newherminetincture",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_old_password"

    @pytest.mark.htmx()
    async def test_update_new_passwords_dont_match(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/password",
            cookies=cookies,
            data={
                "old_password": "herminetincture",
                "new_password": "newherminetincture",
                "new_password_confirm": "newtincturehermine",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "passwords_dont_match"

    @pytest.mark.htmx()
    async def test_update_valid(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/password",
            cookies=cookies,
            data={
                "old_password": "herminetincture",
                "new_password": "newherminetincture",
                "new_password_confirm": "newherminetincture",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestAuthEmailChange:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/email/change"
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert (
            response.headers["Location"]
            == f"http://api.fief.dev{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/email/change", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://api.fief.dev/login"

    @pytest.mark.htmx()
    async def test_valid_get(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/email/change", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        email_input = html.find("input", {"type": "email"})
        assert email_input is not None
        password_input = html.find("input", {"type": "password"})
        assert password_input is not None

    @pytest.mark.htmx()
    async def test_post_invalid_current_password(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/email/change",
            cookies=cookies,
            data={
                "email": "anne+updated@bretagne.duchy",
                "current_password": "INVALID_PASSWORD",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_current_password"

    @pytest.mark.htmx()
    async def test_post_existing_email_address(
        self, test_client_auth_csrf: httpx.AsyncClient, csrf_token: str
    ):
        session_token = session_token_tokens["regular"]
        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]

        response = await test_client_auth_csrf.post(
            "/email/change",
            cookies=cookies,
            data={
                "email": "isabeau@bretagne.duchy",
                "current_password": "herminetincture",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_already_exists"

    @pytest.mark.htmx()
    async def test_post_valid(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
        main_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/email/change",
            cookies=cookies,
            data={
                "email": "anne+updated@bretagne.duchy",
                "current_password": "herminetincture",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "/email/verify" in response.headers["HX-Location"]

        await email_verification_requested_assertions(
            user=tenant_params.user,
            email="anne+updated@bretagne.duchy",
            send_task_mock=send_task_mock,
            session=main_session,
        )


@pytest.mark.asyncio
class TestAuthEmailVerify:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/email/verify"
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert (
            response.headers["Location"]
            == f"http://api.fief.dev{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/email/verify", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://api.fief.dev/login"

    @pytest.mark.htmx()
    async def test_valid_get(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.get(
            f"{tenant_params.path_prefix}/email/verify", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        code_inputs = html.find_all("input", type="text")
        assert len(code_inputs) == settings.email_verification_code_length

    @pytest.mark.htmx()
    async def test_post_invalid_code(
        self,
        tenant_params: TenantParams,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]
        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/email/verify",
            cookies=cookies,
            data={
                "code": "ABCDEF",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_code"

    @pytest.mark.htmx()
    async def test_post_valid(
        self,
        csrf_token: str,
        test_client_auth_csrf: httpx.AsyncClient,
        main_session: AsyncSession,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        code = email_verification_codes["regular_update_email"][0]
        email_verification = test_data["email_verifications"]["regular_update_email"]

        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]
        response = await test_client_auth_csrf.post(
            f"{path_prefix}/email/verify",
            cookies=cookies,
            data={
                "code": code,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "/" in response.headers["HX-Location"]

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
