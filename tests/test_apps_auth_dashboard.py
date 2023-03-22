import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import UserRepository
from fief.settings import settings
from tests.data import TestData, session_token_tokens
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthUpdateProfile:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth_csrf: httpx.AsyncClient
    ):
        response = await test_client_auth_csrf.get(f"{tenant_params.path_prefix}/")

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert (
            response.headers["Location"]
            == f"http://bretagne.localhost:8000{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://bretagne.localhost:8000/login"

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
        email_input = html.find("input", {"id": "email"})
        assert email_input is not None

    @pytest.mark.htmx()
    async def test_update_existing_email_address(
        self, test_client_auth_csrf: httpx.AsyncClient, csrf_token: str
    ):
        session_token = session_token_tokens["regular"]
        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]

        response = await test_client_auth_csrf.post(
            "/",
            cookies=cookies,
            data={
                "email": "isabeau@bretagne.duchy",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_already_exists"

    @pytest.mark.htmx()
    async def test_update_email(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        session_token = session_token_tokens["regular"]
        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]

        response = await test_client_auth_csrf.post(
            "/",
            cookies=cookies,
            data={
                "email": "anne+updated@bretagne.duchy",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(test_data["users"]["regular"].id)
        assert user is not None
        assert user.email == "anne+updated@bretagne.duchy"

    @pytest.mark.htmx()
    async def test_update_fields(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        session_token = session_token_tokens["regular"]
        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]

        response = await test_client_auth_csrf.post(
            "/",
            cookies=cookies,
            data={
                "email": "anne@bretagne.duchy",
                "fields.given_name": "Isabeau",
                "fields.gender": "F",
                "fields.onboarding_done": True,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(test_data["users"]["regular"].id)
        assert user is not None
        assert user.fields["given_name"] == "Isabeau"
        assert user.fields["gender"] == "F"
        assert user.fields["onboarding_done"] is False  # Non-updatable field


@pytest.mark.asyncio
@pytest.mark.workspace_host
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
            == f"http://bretagne.localhost:8000{tenant_params.path_prefix}/login"
        )

    async def test_authenticated_on_another_tenant(
        self, test_client_auth_csrf: httpx.AsyncClient
    ):
        session_token = session_token_tokens["regular_secondary"]

        cookies = {}
        cookies[settings.session_cookie_name] = session_token[0]
        response = await test_client_auth_csrf.get("/password", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == "http://bretagne.localhost:8000/login"

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
                "new_password": "NEW_PASSWORD",
                "new_password_confirm": "NEW_PASSWORD",
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
                "old_password": "hermine",
                "new_password": "NEW_PASSWORD",
                "new_password_confirm": "ANOTHER_NEW_PASSWORD",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "passwords_dont_match"

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
                "old_password": "hermine",
                "new_password": "a",
                "new_password_confirm": "a",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_password"

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
                "old_password": "hermine",
                "new_password": "NEW_PASSWORD",
                "new_password_confirm": "NEW_PASSWORD",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK
