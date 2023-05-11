import urllib.parse
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.models import RegistrationSessionFlow, UserField, UserFieldType, Workspace
from fief.repositories import (
    OAuthAccountRepository,
    RegistrationSessionRepository,
    SessionTokenRepository,
    UserRepository,
)
from fief.settings import settings
from fief.tasks import on_after_register
from tests.data import TestData
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetRegister:
    async def test_invalid_login_session(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_disabled_registration_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["registration_disabled"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            f"{path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "registration_disabled"

    async def test_valid_no_login_session(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        path_prefix = tenant.slug if not tenant.default else ""

        response = await test_client_auth.get(f"{path_prefix}/register")

        assert response.status_code == status.HTTP_200_OK

        html = response.text
        assert 'name="password"' in html

        registration_session_cookie = response.cookies[
            settings.registration_session_cookie_name
        ]
        registration_session_repository = RegistrationSessionRepository(
            workspace_session
        )
        registration_session = await registration_session_repository.get_by_token(
            registration_session_cookie
        )
        assert registration_session is not None
        assert registration_session.flow == RegistrationSessionFlow.PASSWORD
        assert registration_session.tenant_id == tenant.id

    async def test_valid_no_registration_session(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
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

        html = response.text
        assert 'name="password"' in html

        registration_session_cookie = response.cookies[
            settings.registration_session_cookie_name
        ]
        registration_session_repository = RegistrationSessionRepository(
            workspace_session
        )
        registration_session = await registration_session_repository.get_by_token(
            registration_session_cookie
        )
        assert registration_session is not None
        assert registration_session.flow == RegistrationSessionFlow.PASSWORD
        assert registration_session.tenant_id == tenant.id

    async def test_registration_session_from_another_tenant(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        registration_session = test_data["registration_sessions"]["secondary_password"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth.get(
            f"{path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = response.text
        assert 'name="password"' in html

        registration_session_cookie = response.cookies[
            settings.registration_session_cookie_name
        ]
        registration_session_repository = RegistrationSessionRepository(
            workspace_session
        )
        new_registration_session = await registration_session_repository.get_by_token(
            registration_session_cookie
        )
        assert new_registration_session is not None
        assert new_registration_session.id != registration_session.id
        assert new_registration_session.flow == RegistrationSessionFlow.PASSWORD
        assert new_registration_session.tenant_id == tenant.id

    async def test_valid_registration_session_oauth(
        self, test_client_auth: httpx.AsyncClient, tenant_params: TenantParams
    ):
        login_session = tenant_params.login_session
        registration_session = tenant_params.registration_session_oauth

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

        html = response.text
        assert 'name="password"' not in html

        assert registration_session.oauth_account is not None
        assert f'value="{registration_session.email}"' in html


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestPostRegister:
    async def test_invalid_login_session(
        self,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_disabled_registration_tenant(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["registration_disabled"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "registration_disabled"

    @pytest.mark.parametrize("cookie", [None, "INVALID_REGISTRATION_SESSION"])
    async def test_invalid_registration_session(
        self,
        cookie: str | None,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        login_session = tenant_params.login_session
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.registration_session_cookie_name] = cookie

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email and password"),
            pytest.param({"email": "anne@bretagne.duchy"}, id="Missing password"),
            pytest.param({"password": "herminetincture"}, id="Missing email"),
            pytest.param(
                {"email": "anne", "password": "herminetincture"}, id="Invalid email"
            ),
            pytest.param(
                {"email": "anne@bretagne.duchy", "password": "h"},
                id="Too short password",
            ),
            pytest.param(
                {"email": "anne@bretagne.duchy", "password": "h" * 512},
                id="Too long password",
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
        login_session = tenant_params.login_session
        registration_session = tenant_params.registration_session_password
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/register",
            data={**data, "csrf_token": csrf_token},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_user(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        registration_session = test_data["registration_sessions"]["default_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            "/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "REGISTER_USER_ALREADY_EXISTS"

    async def test_new_user(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        login_session = test_data["login_sessions"]["default"]
        registration_session = test_data["registration_sessions"]["default_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            "/register",
            data={
                "email": "louis@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/consent")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        login_hint_cookie = response.cookies[settings.login_hint_cookie_name]
        assert urllib.parse.unquote(login_hint_cookie) == "louis@bretagne.duchy"

        registration_session_repository = RegistrationSessionRepository(
            workspace_session
        )
        deleted_registration_session = await registration_session_repository.get_by_id(
            registration_session.id
        )
        assert deleted_registration_session is None

        send_task_mock.assert_called_with(
            on_after_register, str(session_token.user_id), str(workspace.id)
        )

    async def test_new_user_no_login_session(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        registration_session = test_data["registration_sessions"]["default_password"]
        cookies = {}
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            "/register",
            data={
                "email": "louis@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/")

    async def test_no_email_conflict_on_another_tenant(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        registration_session = test_data["registration_sessions"]["secondary_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

    async def test_registration_fields_set(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        registration_session = test_data["registration_sessions"]["secondary_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "fields.given_name": "Anne",
                "fields.address.line1": "4 place Marc Elder",
                "fields.address.postal_code": "44000",
                "fields.address.city": "Nantes",
                "fields.address.country": "FR",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(session_token.user_id)
        assert user is not None
        assert user.fields == {
            "given_name": "Anne",
            "address": {
                "line1": "4 place Marc Elder",
                "line2": None,
                "postal_code": "44000",
                "city": "Nantes",
                "state": None,
                "country": "FR",
            },
            "onboarding_done": False,  # Default value
        }

    @pytest.mark.parametrize(
        "data,status_code",
        [
            ({}, status.HTTP_400_BAD_REQUEST),
            ({"fields.terms": ""}, status.HTTP_400_BAD_REQUEST),
            ({"fields.terms": "on"}, status.HTTP_302_FOUND),
        ],
    )
    async def test_required_boolean_field(
        self,
        data: dict[str, Any],
        status_code: int,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        field = UserField(
            name="Accept terms",
            slug="terms",
            type=UserFieldType.BOOLEAN,
            configuration={
                "choices": None,
                "default": False,
                "at_registration": True,
                "at_update": False,
                "required": True,
            },
        )
        workspace_session.add(field)
        await workspace_session.commit()

        login_session = test_data["login_sessions"]["secondary"]
        registration_session = test_data["registration_sessions"]["secondary_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
                **data,
            },
            cookies=cookies,
        )

        assert response.status_code == status_code

    async def test_registration_fields_empty_string(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        registration_session = test_data["registration_sessions"]["secondary_password"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "fields.given_name": "",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(session_token.user_id)
        assert user is not None
        assert user.fields == {
            "onboarding_done": False,  # Default value
        }

    async def test_new_user_oauth(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        login_session = test_data["login_sessions"]["default"]
        registration_session = test_data["registration_sessions"]["default_oauth"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            "/register",
            data={
                "email": "louis@bretagne.duchy",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/consent")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        oauth_account_repository = OAuthAccountRepository(workspace_session)
        assert registration_session.oauth_account_id is not None
        oauth_account = await oauth_account_repository.get_by_id(
            registration_session.oauth_account_id
        )
        assert oauth_account is not None
        assert oauth_account.user_id == session_token.user_id

        login_hint_cookie = response.cookies[settings.login_hint_cookie_name]
        assert login_hint_cookie == str(oauth_account.oauth_provider_id)

        registration_session_repository = RegistrationSessionRepository(
            workspace_session
        )
        deleted_registration_session = await registration_session_repository.get_by_id(
            registration_session.id
        )
        assert deleted_registration_session is None

        send_task_mock.assert_called_with(
            on_after_register, str(session_token.user_id), str(workspace.id)
        )

    async def test_new_user_oauth_override_default_email(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        registration_session = test_data["registration_sessions"]["default_oauth"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.registration_session_cookie_name] = registration_session.token

        response = await test_client_auth_csrf.post(
            "/register",
            data={
                "email": "louis+fief@bretagne.duchy",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        user_repository = UserRepository(workspace_session)
        user = await user_repository.get_by_id(session_token.user_id)
        assert user is not None
        assert user.email == "louis+fief@bretagne.duchy"
