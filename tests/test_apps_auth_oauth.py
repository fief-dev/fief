import urllib.parse
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status
from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError
from pytest_mock import MockerFixture

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.models import RegistrationSessionFlow
from fief.repositories import (
    OAuthAccountRepository,
    OAuthSessionRepository,
    RegistrationSessionRepository,
    SessionTokenRepository,
    TenantRepository,
)
from fief.settings import settings
from tests.data import TestData


@pytest.mark.asyncio
class TestOAuthAuthorize:
    async def test_missing_tenant_id(
        self, test_data: TestData, test_client_auth: httpx.AsyncClient
    ):
        login_session = test_data["login_sessions"]["default"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get("/oauth/authorize", cookies=cookies)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unknown_tenant_id(
        self,
        test_data: TestData,
        test_client_auth: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        login_session = test_data["login_sessions"]["default"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize", params={"tenant": str(not_existing_uuid)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_tenant"

    async def test_invalid_login_session(
        self,
        test_data: TestData,
        test_client_auth: httpx.AsyncClient,
        main_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]

        oauth_provider = test_data["oauth_providers"]["google"]
        tenant_repository = TenantRepository(main_session)
        tenant.oauth_providers = [oauth_provider]
        await tenant_repository.update(tenant)

        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={"tenant": str(tenant.id), "provider": str(oauth_provider.id)},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_invalid_oauth_provider(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={"tenant": str(tenant.id), "provider": str(not_existing_uuid)},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_provider"

    async def test_invalid_oauth_provider_for_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={
                "tenant": str(tenant.id),
                "provider": str(test_data["oauth_providers"]["google"].id),
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_provider"

    async def test_expired_login_session(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["expired"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        oauth_provider = test_data["oauth_providers"]["google"]
        tenant_repository = TenantRepository(main_session)
        tenant.oauth_providers = [oauth_provider]
        await tenant_repository.update(tenant)

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={"tenant": str(tenant.id), "provider": str(oauth_provider.id)},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER

        location = response.headers["Location"]
        assert location.startswith(f"http://api.fief.dev{path_prefix}/authorize")

    @pytest.mark.parametrize("has_login_session", [False, True])
    async def test_valid(
        self,
        has_login_session: bool,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant

        oauth_provider = test_data["oauth_providers"]["google"]
        tenant_repository = TenantRepository(main_session)
        tenant.oauth_providers = [oauth_provider]
        await tenant_repository.update(tenant)

        cookies = {}
        if has_login_session:
            cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={"tenant": str(tenant.id), "provider": str(oauth_provider.id)},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        parsed_location = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed_location.query)

        state = query_params["state"][0]
        redirect_uri = query_params["redirect_uri"][0]
        scope = query_params["scope"][0]

        repository = OAuthSessionRepository(main_session)
        oauth_session = await repository.get_by_token(state)

        assert oauth_session is not None
        assert oauth_session.oauth_provider_id == oauth_provider.id
        assert oauth_session.tenant_id == tenant.id

        assert set(scope.split(" ")) == {
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "custom_scope",
        }

        assert oauth_session.redirect_uri == redirect_uri
        assert redirect_uri.endswith("/oauth/callback")

    async def test_valid_secondary_tenant(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        client = login_session.client
        tenant = client.tenant

        oauth_provider = test_data["oauth_providers"]["google"]
        tenant_repository = TenantRepository(main_session)
        tenant.oauth_providers = [oauth_provider]
        await tenant_repository.update(tenant)

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/authorize",
            params={"tenant": str(tenant.id), "provider": str(oauth_provider.id)},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND


@pytest.mark.asyncio
class TestOAuthCallback:
    @pytest.mark.parametrize(
        "params,error",
        [
            pytest.param(
                {
                    "error": "ERROR",
                },
                "oauth_error",
                id="OAuth error",
            ),
            pytest.param(
                {},
                "missing_code",
                id="Missing code",
            ),
            pytest.param(
                {
                    "code": "CODE",
                },
                "invalid_session",
                id="Missing state",
            ),
            pytest.param(
                {"code": "CODE", "state": "INVALID_STATE"},
                "invalid_session",
                id="Invalid state",
            ),
        ],
    )
    async def test_redirect_error(
        self,
        test_client_auth: httpx.AsyncClient,
        params: dict[str, str],
        error: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/callback", params=params, cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == error

    async def test_access_token_error(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        oauth_session = test_data["oauth_sessions"]["default_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = GetAccessTokenError()
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "access_token_error"

    async def test_get_id_email_error(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        oauth_session = test_data["oauth_sessions"]["default_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = GetIdEmailError(
            {"error": "error_message"}
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "id_email_error"

    async def test_existing_oauth_account_inactive(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]

        oauth_session = test_data["oauth_sessions"]["default_google"]
        oauth_account = test_data["oauth_accounts"]["inactive_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = AsyncMock(
            return_value=(oauth_account.account_id, oauth_account.account_email)
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "inactive_user"

    @pytest.mark.parametrize("has_login_session", [False, True])
    async def test_existing_oauth_account(
        self,
        has_login_session: bool,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        oauth_session = test_data["oauth_sessions"]["default_google"]
        oauth_account = test_data["oauth_accounts"]["regular_google"]

        cookies = {}
        if has_login_session:
            cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = AsyncMock(
            return_value=(oauth_account.account_id, oauth_account.account_email)
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]

        if has_login_session:
            assert redirect_uri.endswith(f"{path_prefix}/consent")
        else:
            assert redirect_uri.endswith(f"{path_prefix}/")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(main_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        login_hint_cookie = response.cookies[settings.login_hint_cookie_name]
        assert login_hint_cookie == str(oauth_account.oauth_provider_id)

        oauth_account_repository = OAuthAccountRepository(main_session)
        updated_oauth_account = await oauth_account_repository.get_by_id(
            oauth_account.id
        )
        assert updated_oauth_account is not None
        assert updated_oauth_account.access_token == "ACCESS_TOKEN"
        assert updated_oauth_account.refresh_token == "REFRESH_TOKEN"
        assert updated_oauth_account.expires_at is not None
        assert oauth_account.expires_at is not None
        assert updated_oauth_account.expires_at > oauth_account.expires_at

    async def test_dangling_account(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        oauth_session = test_data["oauth_sessions"]["default_google"]
        oauth_account = test_data["oauth_accounts"]["new_user_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = AsyncMock(
            return_value=(oauth_account.account_id, oauth_account.account_email)
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/register")

        oauth_account_repository = OAuthAccountRepository(main_session)
        updated_oauth_account = (
            await oauth_account_repository.get_by_provider_and_account_id(
                oauth_session.oauth_provider_id, oauth_account.account_id
            )
        )
        assert updated_oauth_account is not None
        assert updated_oauth_account.id == oauth_account.id
        assert updated_oauth_account.access_token == "ACCESS_TOKEN"
        assert updated_oauth_account.refresh_token == "REFRESH_TOKEN"
        assert updated_oauth_account.user is None

        registration_session_cookie = response.cookies[
            settings.registration_session_cookie_name
        ]
        registration_session_repository = RegistrationSessionRepository(main_session)
        registration_session = await registration_session_repository.get_by_token(
            registration_session_cookie
        )
        assert registration_session is not None
        assert registration_session.flow == RegistrationSessionFlow.OAUTH
        assert registration_session.oauth_account_id == updated_oauth_account.id
        assert registration_session.email == updated_oauth_account.account_email

    async def test_new_account(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        oauth_session = test_data["oauth_sessions"]["default_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = AsyncMock(
            return_value=("NEW_ACCOUNT", "louis@bretagne.duchy")
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/register")

        oauth_account_repository = OAuthAccountRepository(main_session)
        oauth_account = await oauth_account_repository.get_by_provider_and_account_id(
            oauth_session.oauth_provider_id, "NEW_ACCOUNT"
        )
        assert oauth_account is not None
        assert oauth_account.access_token == "ACCESS_TOKEN"
        assert oauth_account.refresh_token == "REFRESH_TOKEN"
        assert oauth_account.user is None

        registration_session_cookie = response.cookies[
            settings.registration_session_cookie_name
        ]
        registration_session_repository = RegistrationSessionRepository(main_session)
        registration_session = await registration_session_repository.get_by_token(
            registration_session_cookie
        )
        assert registration_session is not None
        assert registration_session.flow == RegistrationSessionFlow.OAUTH
        assert registration_session.oauth_account_id == oauth_account.id
        assert registration_session.email == oauth_account.account_email

    async def test_secondary_tenant_invalid_login_session(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        oauth_session = test_data["oauth_sessions"]["secondary_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_secondary_tenant(
        self,
        mocker: MockerFixture,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["secondary"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        oauth_session = test_data["oauth_sessions"]["secondary_google"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.get_access_token.side_effect = AsyncMock(
            return_value={
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(datetime.now(UTC).timestamp() + 3600),
                "refresh_token": "REFRESH_TOKEN",
            }
        )
        oauth_provider_service_mock.get_id_email.side_effect = AsyncMock(
            return_value=("NEW_ACCOUNT", "louis@bretagne.duchy")
        )
        mocker.patch(
            "fief.apps.auth.routers.oauth.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        response = await test_client_auth.get(
            "/oauth/callback",
            params={
                "code": "CODE",
                "redirect_uri": oauth_session.redirect_uri,
                "state": oauth_session.token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/register")
