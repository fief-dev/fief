from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.managers import SessionTokenManager, UserManager
from fief.models import UserField, UserFieldType, Workspace
from fief.settings import settings
from fief.tasks import on_after_register
from tests.data import TestData
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetRegister:
    @pytest.mark.parametrize("cookie", [None, "INVALID_LOGIN_SESSION"])
    async def test_invalid_login_session(
        self,
        cookie: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        cookies = {}
        if cookie is not None:
            cookies[settings.login_session_cookie_name] = cookie

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/register", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
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


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestPostRegister:
    @pytest.mark.parametrize("cookie", [None, "INVALID_LOGIN_SESSION"])
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
            f"{tenant_params.path_prefix}/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email and password"),
            pytest.param({"email": "anne@bretagne.duchy"}, id="Missing password"),
            pytest.param({"password": "hermine1"}, id="Missing email"),
            pytest.param({"email": "anne", "password": "hermine1"}, id="Invalid email"),
            pytest.param(
                {"email": "anne@bretagne.duchy", "password": "h"}, id="Invalid password"
            ),
        ],
    )
    async def test_invalid_form(
        self,
        data: Dict[str, str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        login_session = tenant_params.login_session
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/register", data=data, cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_user(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "REGISTER_USER_ALREADY_EXISTS"

    async def test_new_user(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        login_session = test_data["login_sessions"]["default"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            "/register",
            data={"email": "louis@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith("/consent")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_manager = SessionTokenManager(workspace_session)
        session_token = await session_token_manager.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        send_task_mock.assert_called_once_with(
            on_after_register, str(session_token.user_id), str(workspace.id)
        )

    async def test_no_email_conflict_on_another_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["secondary"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

    async def test_registration_fields_set(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "hermine1",
                "fields.given_name": "Anne",
                "fields.address.line1": "4 place Marc Elder",
                "fields.address.postal_code": "44000",
                "fields.address.city": "Nantes",
                "fields.address.country": "FR",
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_manager = SessionTokenManager(workspace_session)
        session_token = await session_token_manager.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        user_manager = UserManager(workspace_session)
        user = await user_manager.get_by_id(session_token.user_id)
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
            ({"fields.terms": "off"}, status.HTTP_400_BAD_REQUEST),
            ({"fields.terms": "on"}, status.HTTP_302_FOUND),
        ],
    )
    async def test_required_boolean_field(
        self,
        data: Dict[str, Any],
        status_code: int,
        test_client_auth: httpx.AsyncClient,
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
        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={
                "email": "anne@bretagne.duchy",
                "password": "hermine1",
                **data,
            },
            cookies=cookies,
        )

        assert response.status_code == status_code
