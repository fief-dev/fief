import urllib.parse
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.crypto.token import get_token_hash
from fief.crypto.verify_code import get_verify_code_hash
from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import (
    EmailVerificationRepository,
    GrantRepository,
    LoginSessionRepository,
    SessionTokenRepository,
    UserRepository,
)
from fief.services.response_type import DEFAULT_RESPONSE_MODE, HYBRID_RESPONSE_TYPES
from fief.settings import settings
from fief.tasks import on_email_verification_requested
from tests.data import TestData, email_verification_codes, session_token_tokens
from tests.helpers import authorization_code_assertions, get_params_by_response_mode
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthAuthorize:
    @pytest.mark.parametrize(
        "params,error",
        [
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                },
                "invalid_client",
                id="Missing client_id",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "INVALID_CLIENT_ID",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                },
                "invalid_client",
                id="Invalid client",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "VALID_CLIENT_ID",
                    "scope": "openid",
                },
                "invalid_redirect_uri",
                id="Missing redirect_uri",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "client_id": "VALID_CLIENT_ID",
                    "redirect_uri": "https://bordeaux.city/callback",
                    "scope": "openid",
                },
                "invalid_redirect_uri",
                id="Not authorized redirect_uri",
            ),
        ],
    )
    async def test_authorize_error(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        params: dict[str, str],
        error: str,
    ):
        # Trick to set a valid client_id for the current tenant
        params = {**params}
        if params.get("client_id") == "VALID_CLIENT_ID":
            params["client_id"] = tenant_params.client.client_id

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == error

    @pytest.mark.parametrize(
        "params,error",
        [
            pytest.param(
                {
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                },
                "invalid_request",
                id="Missing response_type",
            ),
            pytest.param(
                {
                    "response_type": "magic_wand",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                },
                "invalid_request",
                id="Invalid response_type",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                },
                "invalid_request",
                id="Missing scope",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "user",
                },
                "invalid_scope",
                id="Missing openid scope",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "prompt": "INVALID_PROMPT",
                },
                "invalid_request",
                id="Invalid prompt",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "prompt": "none",
                },
                "login_required",
                id="None prompt without session",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "prompt": "consent",
                },
                "login_required",
                id="Consent prompt without session",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "screen": "INVALID_SCREEN",
                },
                "invalid_request",
                id="Invalid screen",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "request": "REQUEST_PARAMETER",
                },
                "request_not_supported",
                id="Use of unsupported request parameter",
            ),
            pytest.param(
                {
                    "response_type": "code id_token",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "request": "REQUEST_PARAMETER",
                },
                "request_not_supported",
                id="Use of unsupported request parameter with a Hybrid flow without nonce",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "redirect_uri": "https://nantes.city/callback",
                    "scope": "openid",
                    "code_challenge": "CODE_CHALLENGE",
                    "code_challenge_method": "UNSUPPORTED_METHOD",
                },
                "invalid_request",
                id="Invalid code_challenge_method",
            ),
            *[
                pytest.param(
                    {
                        "response_type": response_type,
                        "redirect_uri": "https://nantes.city/callback",
                        "scope": "openid",
                    },
                    "invalid_request",
                    id=f"Missing nonce in Hybrid flow with {response_type}",
                )
                for response_type in HYBRID_RESPONSE_TYPES
            ],
        ],
    )
    async def test_authorize_redirect_error(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        params: dict[str, str],
        error: str,
    ):
        params = {
            **params,
            "client_id": tenant_params.client.client_id,
        }

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]

        assert redirect_uri.startswith("https://nantes.city/callback")

        try:
            response_mode = DEFAULT_RESPONSE_MODE[params["response_type"]]
        except KeyError:
            response_mode = "query"
        redirect_params = get_params_by_response_mode(redirect_uri, response_mode)
        assert redirect_params["error"] == error

    async def test_client_tenant_mismatch(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        params = {
            "response_type": "code",
            "client_id": test_data["clients"]["secondary_tenant"].client_id,
            "redirect_uri": "https://nantes.city/callback",
            "scope": "openid",
        }

        response = await test_client_auth.get("/authorize", params=params)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_client"

    @pytest.mark.parametrize(
        "params,session,redirection",
        [
            pytest.param(
                {"response_type": "code"}, False, "/login", id="Default login screen"
            ),
            pytest.param(
                {"response_type": "code", "screen": "login"},
                False,
                "/login",
                id="Login screen",
            ),
            pytest.param(
                {"response_type": "code", "screen": "register"},
                False,
                "/register",
                id="Register screen",
            ),
            pytest.param(
                {"response_type": "code"}, True, "/consent", id="No prompt with session"
            ),
            pytest.param(
                {"response_type": "code", "prompt": "none"},
                True,
                "/consent",
                id="None prompt with session",
            ),
            pytest.param(
                {"response_type": "code", "prompt": "consent"},
                True,
                "/consent",
                id="Consent prompt with session",
            ),
            pytest.param(
                {"response_type": "code", "prompt": "login"},
                True,
                "/login",
                id="Login prompt with session",
            ),
            pytest.param(
                {"response_type": "code", "nonce": "NONCE"},
                False,
                "/login",
                id="Provided nonce value",
            ),
            pytest.param(
                {"response_type": "code", "max_age": 3600},
                True,
                "/consent",
                id="max_age one hour ago",
            ),
            pytest.param(
                {"response_type": "code", "max_age": 0},
                True,
                "/login",
                id="max_age now",
            ),
            pytest.param(
                {"response_type": "code", "code_challenge": "CODE_CHALLENGE"},
                False,
                "/login",
                id="code_challenge without method",
            ),
            pytest.param(
                {
                    "response_type": "code",
                    "code_challenge": "CODE_CHALLENGE",
                    "code_challenge_method": "S256",
                },
                False,
                "/login",
                id="code_challenge with specified method",
            ),
            *[
                pytest.param(
                    {
                        "response_type": response_type,
                        "nonce": "NONCE",
                    },
                    False,
                    "/login",
                    id=f"Hybrid flow with {response_type}",
                )
                for response_type in HYBRID_RESPONSE_TYPES
            ],
        ],
    )
    async def test_valid(
        self,
        params: dict[str, str],
        session: bool,
        redirection: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
        workspace_session: AsyncSession,
    ):
        params = {
            **params,
            "client_id": tenant_params.client.client_id,
            "redirect_uri": "https://nantes.city/callback",
            "scope": "openid",
        }

        cookies = {}
        if session:
            cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params, cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location.endswith(f"{tenant_params.path_prefix}{redirection}")

        login_session_cookie = response.cookies[settings.login_session_cookie_name]
        login_session_repository = LoginSessionRepository(workspace_session)
        login_session = await login_session_repository.get_by_token(
            login_session_cookie
        )
        assert login_session is not None

        if "nonce" in params:
            assert login_session.nonce == params["nonce"]

        if "code_challenge" in params:
            assert login_session.code_challenge == params["code_challenge"]
            if "code_challenge_method" in params:
                assert (
                    login_session.code_challenge_method
                    == params["code_challenge_method"]
                )
            else:
                assert login_session.code_challenge_method == "plain"

        if params["response_type"] in ["code"]:
            assert login_session.response_mode == "query"
        else:
            assert login_session.response_mode == "fragment"

    async def test_set_locale_by_query(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        params = {
            "lang": "fr_FR",
            "response_type": "code",
            "client_id": tenant_params.client.client_id,
            "redirect_uri": "https://nantes.city/callback",
            "scope": "openid",
        }

        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params, cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND
        assert response.cookies[settings.user_locale_cookie_name] == "fr_FR"

    @pytest.mark.parametrize(
        "login_hint", ["anne@bretagne.duchy", "b0133c88-04fa-4653-8dcc-4bf6c49d2d25"]
    )
    async def test_set_login_hint_by_query(
        self,
        login_hint: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        params = {
            "login_hint": login_hint,
            "response_type": "code",
            "client_id": tenant_params.client.client_id,
            "redirect_uri": "https://nantes.city/callback",
            "scope": "openid",
        }

        cookies = {}
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/authorize", params=params, cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND
        assert (
            urllib.parse.unquote(response.cookies[settings.login_hint_cookie_name])
            == login_hint
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthGetLogin:
    async def test_invalid_login_session(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/login", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_missing_login_session(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/login")

        assert response.status_code == status.HTTP_200_OK

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth.get(f"{path_prefix}/login", cookies=cookies)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthPostLogin:
    async def test_invalid_login_session(
        self,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/login", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    async def test_bad_credentials(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/login",
            data={
                "email": "anne@bretagne.duchy",
                "password": "foo",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "bad_credentials"

    async def test_valid(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/login",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/verify-request")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert session_token is not None

        login_hint_cookie = response.cookies[settings.login_hint_cookie_name]
        assert urllib.parse.unquote(login_hint_cookie) == "anne@bretagne.duchy"

    async def test_valid_with_session(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token = test_data["session_tokens"]["regular"]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/login",
            data={
                "email": "anne@bretagne.duchy",
                "password": "herminetincture",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/verify-request")

        session_cookie = response.cookies[settings.session_cookie_name]
        session_token_repository = SessionTokenRepository(workspace_session)
        new_session_token = await session_token_repository.get_by_token(
            get_token_hash(session_cookie)
        )
        assert new_session_token is not None
        assert new_session_token.id != session_token.id

        old_session_token = await session_token_repository.get_by_id(session_token.id)
        assert old_session_token is None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthVerifyEmailRequest:
    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_invalid_session_token(
        self,
        cookie: str | None,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        response = await test_client_auth.get(
            f"{path_prefix}/verify-request", cookies=cookies
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/login")

    async def test_already_verified_no_login_session(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]

        response = await test_client_auth.get(
            f"{path_prefix}/verify-request", cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND
        redirect_uri = response.headers["Location"]

        assert redirect_uri.endswith(f"{path_prefix}/")

    async def test_already_verified_login_session(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        cookies = {}
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]

        response = await test_client_auth.get(
            f"{path_prefix}/verify-request", cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND
        redirect_uri = response.headers["Location"]

        assert redirect_uri.endswith(f"{path_prefix}/consent")

    async def test_not_verified(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        user = test_data["users"]["not_verified_email"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens[
            "not_verified_email"
        ][0]

        response = await test_client_auth.get(
            f"{path_prefix}/verify-request", cookies=cookies
        )

        assert response.status_code == status.HTTP_302_FOUND
        redirect_uri = response.headers["Location"]

        assert redirect_uri.endswith(f"{path_prefix}/verify")

        email_verification_repository = EmailVerificationRepository(workspace_session)
        email_verifications = await email_verification_repository.all()
        email_verification = email_verifications[-1]
        assert email_verification.email == user.email

        send_task_mock.assert_called_once()
        assert send_task_mock.call_args[0][0] == on_email_verification_requested
        assert send_task_mock.call_args[0][1] == str(email_verification.id)
        assert send_task_mock.call_args[0][2] == str(workspace.id)
        assert (
            get_verify_code_hash(send_task_mock.call_args[0][3])
            == email_verification.code
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthGetVerifyEmail:
    async def test_invalid_login_session(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/verify", cookies=cookies
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_invalid_session_token(
        self,
        cookie: str | None,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        response = await test_client_auth.get(f"{path_prefix}/verify", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/login")

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["not_verified_email"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens[
            "not_verified_email"
        ][0]

        response = await test_client_auth.get(f"{path_prefix}/verify", cookies=cookies)

        assert response.status_code == status.HTTP_200_OK
        html = BeautifulSoup(response.text, features="html.parser")
        code_inputs = html.find_all("input", type="text")
        assert len(code_inputs) == settings.email_verification_code_length


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthPostVerifyEmail:
    async def test_invalid_login_session(
        self,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = "INVALID_LOGIN_SESSION"
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/verify",
            data={"code": "ABCDEF", "csrf_token": csrf_token},
            cookies=cookies,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_session"

    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_invalid_session_token(
        self,
        cookie: str | None,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/verify",
            data={"code": "ABCDEF", "csrf_token": csrf_token},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/login")

    async def test_invalid_code(
        self,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        user = test_data["users"]["not_verified_email"]
        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens[
            "not_verified_email"
        ][0]

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/verify",
            data={"code": "ABCDEF", "csrf_token": csrf_token},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_code"

    @pytest.mark.parametrize(
        "has_login_session,redirect_path",
        [
            (True, "/consent"),
            (False, "/"),
        ],
    )
    async def test_valid(
        self,
        has_login_session: bool,
        redirect_path: str,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        workspace_session: AsyncSession,
        test_data: TestData,
    ):
        user = test_data["users"]["not_verified_email"]
        code = email_verification_codes["not_verified_email"][0]
        email_verification = test_data["email_verifications"]["not_verified_email"]

        tenant = user.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens[
            "not_verified_email"
        ][0]
        if has_login_session:
            login_session = test_data["login_sessions"]["default"]
            cookies[settings.login_session_cookie_name] = login_session.token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/verify",
            data={"code": code, "csrf_token": csrf_token},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}{redirect_path}")

        email_verification_repository = EmailVerificationRepository(workspace_session)
        deleted_email_verification = await email_verification_repository.get_by_id(
            email_verification.id
        )
        assert deleted_email_verification is None

        user_repository = UserRepository(workspace_session)
        updated_user = await user_repository.get_by_id(user.id)
        assert updated_user is not None
        assert updated_user.email_verified is True


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthGetConsent:
    @pytest.mark.parametrize(
        "cookie,error",
        [(None, "missing_session"), ("INVALID_LOGIN_SESSION", "invalid_session")],
    )
    async def test_missing_invalid_login_session(
        self,
        cookie: str | None,
        error: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        cookies = {}
        if cookie is not None:
            cookies[settings.login_session_cookie_name] = cookie
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/consent", cookies=cookies
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == error

    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_invalid_session_token(
        self,
        cookie: str | None,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        response = await test_client_auth.get(f"{path_prefix}/consent", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/login")

    async def test_valid(
        self, test_client_auth: httpx.AsyncClient, tenant_params: TenantParams
    ):
        cookies = {}
        cookies[settings.login_session_cookie_name] = tenant_params.login_session.token
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/consent", cookies=cookies
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_none_prompt_without_grant(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["default_none_prompt"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth.get(f"{path_prefix}/consent", cookies=cookies)

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.startswith(login_session.redirect_uri)
        redirect_params = get_params_by_response_mode(
            redirect_uri, login_session.response_mode
        )
        assert redirect_params["error"] == "consent_required"
        assert redirect_params["state"] == login_session.state

        login_session_repository = LoginSessionRepository(workspace_session)
        used_login_session = await login_session_repository.get_by_token(
            login_session.token
        )
        assert used_login_session is None

    async def test_granted(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["granted_default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token = test_data["session_tokens"]["regular"]
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth.get(f"{path_prefix}/consent", cookies=cookies)

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        await authorization_code_assertions(
            redirect_uri=redirect_uri,
            login_session=login_session,
            session_token=session_token,
            session=workspace_session,
        )

        set_cookie_header = response.headers["Set-Cookie"]
        assert set_cookie_header.startswith(f'{settings.login_session_cookie_name}=""')
        assert "Max-Age=0" in set_cookie_header

        login_session_repository = LoginSessionRepository(workspace_session)
        used_login_session = await login_session_repository.get_by_token(
            login_session.token
        )
        assert used_login_session is None

    async def test_granted_larger_scope(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        login_session = test_data["login_sessions"]["granted_default_larger_scope"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth.get(f"{path_prefix}/consent", cookies=cookies)

        assert response.status_code == status.HTTP_200_OK

    async def test_first_party(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"]["first_party_default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token = test_data["session_tokens"]["regular"]
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth.get(f"{path_prefix}/consent", cookies=cookies)

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        await authorization_code_assertions(
            redirect_uri=redirect_uri,
            login_session=login_session,
            session_token=session_token,
            session=workspace_session,
        )

        set_cookie_header = response.headers["Set-Cookie"]
        assert set_cookie_header.startswith(f'{settings.login_session_cookie_name}=""')
        assert "Max-Age=0" in set_cookie_header

        login_session_repository = LoginSessionRepository(workspace_session)
        used_login_session = await login_session_repository.get_by_token(
            login_session.token
        )
        assert used_login_session is None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthPostConsent:
    @pytest.mark.parametrize(
        "cookie,error",
        [(None, "missing_session"), ("INVALID_LOGIN_SESSION", "invalid_session")],
    )
    async def test_missing_invalid_login_session(
        self,
        cookie: str | None,
        error: str,
        tenant_params: TenantParams,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
    ):
        cookies = {}
        if cookie is not None:
            cookies[settings.login_session_cookie_name] = cookie
        cookies[settings.session_cookie_name] = tenant_params.session_token_token[0]

        response = await test_client_auth_csrf.post(
            f"{tenant_params.path_prefix}/consent",
            cookies=cookies,
            data={"allow": "allow", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == error

    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_invalid_session_token(
        self,
        cookie: str | None,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
    ):
        login_session = test_data["login_sessions"]["default"]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/consent",
            cookies=cookies,
            data={"allow": "allow", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

        redirect_uri = response.headers["Location"]
        assert redirect_uri.endswith(f"{path_prefix}/login")

    @pytest.mark.parametrize(
        "login_session_alias",
        [
            "default",
            "default_code_challenge_plain",
            "default_code_challenge_s256",
            "default_hybrid_id_token",
            "default_hybrid_token",
            "default_hybrid_id_token_token",
        ],
    )
    async def test_allow(
        self,
        login_session_alias: str,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"][login_session_alias]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token = test_data["session_tokens"]["regular"]
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/consent",
            cookies=cookies,
            data={"allow": "allow", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        await authorization_code_assertions(
            redirect_uri=redirect_uri,
            login_session=login_session,
            session_token=session_token,
            session=workspace_session,
        )

        set_cookie_header = response.headers["Set-Cookie"]
        assert set_cookie_header.startswith(f'{settings.login_session_cookie_name}=""')
        assert "Max-Age=0" in set_cookie_header

        login_session_repository = LoginSessionRepository(workspace_session)
        used_login_session = await login_session_repository.get_by_token(
            login_session.token
        )
        assert used_login_session is None

        grant_repository = GrantRepository(workspace_session)
        grant = await grant_repository.get_by_user_and_client(
            session_token.user_id, client.id
        )
        assert grant is not None
        assert grant.scope == login_session.scope

    @pytest.mark.parametrize(
        "login_session_alias",
        [
            "default",
            "default_hybrid_id_token",
            "default_hybrid_token",
            "default_hybrid_id_token_token",
        ],
    )
    async def test_deny(
        self,
        login_session_alias: str,
        test_client_auth_csrf: httpx.AsyncClient,
        csrf_token: str,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        login_session = test_data["login_sessions"][login_session_alias]
        client = login_session.client
        tenant = client.tenant
        path_prefix = tenant.slug if not tenant.default else ""
        session_token_token = session_token_tokens["regular"][0]

        cookies = {}
        cookies[settings.login_session_cookie_name] = login_session.token
        cookies[settings.session_cookie_name] = session_token_token

        response = await test_client_auth_csrf.post(
            f"{path_prefix}/consent",
            cookies=cookies,
            data={"deny": "deny", "csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_302_FOUND

        redirect_uri = response.headers["Location"]
        assert redirect_uri.startswith(login_session.redirect_uri)
        redirect_params = get_params_by_response_mode(
            redirect_uri, login_session.response_mode
        )
        assert redirect_params["error"] == "access_denied"
        assert redirect_params["state"] == login_session.state

        set_cookie_header = response.headers["Set-Cookie"]
        assert set_cookie_header.startswith(f'{settings.login_session_cookie_name}=""')
        assert "Max-Age=0" in set_cookie_header

        login_session_repository = LoginSessionRepository(workspace_session)
        used_login_session = await login_session_repository.get_by_token(
            login_session.token
        )
        assert used_login_session is None


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestAuthLogout:
    async def test_missing_redirect_uri(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        session_token = test_data["session_tokens"]["regular"]
        tenant = session_token.user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]

        response = await test_client_auth.get(f"{path_prefix}/logout", cookies=cookies)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "invalid_request"

    @pytest.mark.parametrize("cookie", [None, "INVALID_SESSION_TOKEN"])
    async def test_no_session_token(
        self,
        cookie: str | None,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        tenant = test_data["tenants"]["default"]
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        if cookie is not None:
            cookies[settings.session_cookie_name] = cookie

        redirect_uri = "https://www.bretagne.duchy"
        response = await test_client_auth.get(
            f"{path_prefix}/logout",
            params={"redirect_uri": redirect_uri},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == redirect_uri

    async def test_valid_session_token(
        self,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        session_token = test_data["session_tokens"]["regular"]
        tenant = session_token.user.tenant
        path_prefix = tenant.slug if not tenant.default else ""

        cookies = {}
        cookies[settings.session_cookie_name] = session_token_tokens["regular"][0]

        redirect_uri = "https://www.bretagne.duchy"
        response = await test_client_auth.get(
            f"{path_prefix}/logout",
            params={"redirect_uri": redirect_uri},
            cookies=cookies,
        )

        assert response.status_code == status.HTTP_302_FOUND

        location = response.headers["Location"]
        assert location == redirect_uri

        assert "Set-Cookie" in response.headers

        session_token_repository = SessionTokenRepository(workspace_session)
        deleted_session_token = await session_token_repository.get_by_token(
            session_token_tokens["regular"][1]
        )
        assert deleted_session_token is None
