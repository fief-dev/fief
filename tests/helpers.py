import json
import re
from collections.abc import Callable
from datetime import datetime
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status
from furl import furl
from jwcrypto import jwk, jwt

from fief.crypto.id_token import get_validation_hash
from fief.crypto.token import get_token_hash
from fief.crypto.verify_code import get_verify_code_hash
from fief.db import AsyncSession
from fief.models import AuthorizationCode, LoginSession, SessionToken, User
from fief.repositories import AuthorizationCodeRepository, EmailVerificationRepository
from fief.services.acr import ACR
from fief.tasks import on_email_verification_requested

HTTPXResponseAssertion = Callable[[httpx.Response], None]


class StringMatch:
    def __init__(self, pattern: str) -> None:
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, str):
            return False
        return self.pattern.search(o) is not None


def str_match(s: str):
    return StringMatch(s)


class UnorderedListMatch:
    def __init__(self, list_match: list) -> None:
        self.list_match = list_match

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, list):
            return False
        return set(self.list_match) == set(o)


def unordered_list(list_match: list):
    return UnorderedListMatch(list_match)


def api_unauthorized_assertions(response: httpx.Response):
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def dashboard_unauthorized_assertions(response: httpx.Response):
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"].endswith("/auth/login")


def dashboard_forbidden_assertions(response: httpx.Response):
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def access_token_assertions(
    *, access_token: str, jwk: jwk.JWK, user: User, authenticated_at: datetime, acr: ACR
):
    access_token_jwt = jwt.JWT(jwt=access_token, algs=["RS256"], key=jwk)

    access_token_header = json.loads(access_token_jwt.header)
    assert access_token_header["kid"] == jwk["kid"]

    access_token_claims = json.loads(access_token_jwt.claims)

    assert access_token_claims["sub"] == str(user.id)
    assert access_token_claims["auth_time"] == pytest.approx(
        authenticated_at.timestamp(), rel=1e-9
    )
    assert access_token_claims["acr"] == acr
    assert "scope" in access_token_claims
    assert "permissions" in access_token_claims


def security_headers_assertions(response: httpx.Response):
    headers = response.headers
    assert headers["content-security-policy"] == "frame-ancestors 'self'"
    assert headers["x-frame-options"] == "SAMEORIGIN"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["permissions-policy"] == "geolocation=(), camera=(), microphone=()"


async def id_token_assertions(
    *,
    id_token: str,
    jwk: jwk.JWK,
    authenticated_at: datetime,
    acr: ACR,
    authorization_code_tuple: tuple[AuthorizationCode, str] | None = None,
    access_token: str | None = None,
):
    id_token_jwt = jwt.JWT(jwt=id_token, algs=["RS256"], key=jwk)

    id_token_header = json.loads(id_token_jwt.header)
    assert id_token_header["kid"] == jwk["kid"]

    id_token_claims = json.loads(id_token_jwt.claims)

    assert id_token_claims["auth_time"] == pytest.approx(
        authenticated_at.timestamp(), rel=1e-9
    )
    assert id_token_claims["acr"] == acr

    if authorization_code_tuple is not None:
        authorization_code, code = authorization_code_tuple
        if authorization_code.nonce is not None:
            assert id_token_claims["nonce"] == authorization_code.nonce
        else:
            assert "nonce" not in id_token_claims
        assert "c_hash" in id_token_claims
        c_hash = id_token_claims["c_hash"]
        assert c_hash == get_validation_hash(code)

    if access_token is not None:
        assert "at_hash" in id_token_claims


async def encrypted_id_token_assertions(
    *,
    id_token: str,
    sign_jwk: jwk.JWK,
    encrypt_jwk: jwk.JWK,
    authenticated_at: datetime,
    acr: ACR,
    authorization_code_tuple: tuple[AuthorizationCode, str] | None = None,
    access_token: str | None = None,
):
    encrypted_id_token_jwt = jwt.JWT(
        jwt=id_token, algs=["RSA-OAEP-256", "A256CBC-HS512"], key=encrypt_jwk
    )

    encrypted_id_token_header = json.loads(encrypted_id_token_jwt.header)
    assert encrypted_id_token_header["kid"] == encrypt_jwk["kid"]

    await id_token_assertions(
        id_token=encrypted_id_token_jwt.claims,
        jwk=sign_jwk,
        authenticated_at=authenticated_at,
        acr=acr,
        authorization_code_tuple=authorization_code_tuple,
        access_token=access_token,
    )


def get_params_by_response_mode(
    redirect_uri: str, response_mode: str
) -> dict[str, str]:
    parsed_uri = furl(redirect_uri)
    if response_mode == "query":
        return parsed_uri.query.params
    elif response_mode == "fragment":
        return parsed_uri.fragment.query.params
    raise Exception("Unknown response_mode")


async def authorization_code_assertions(
    *,
    redirect_uri: str,
    login_session: LoginSession,
    session_token: SessionToken,
    session: AsyncSession,
):
    assert redirect_uri.startswith(login_session.redirect_uri)
    params = get_params_by_response_mode(redirect_uri, login_session.response_mode)

    assert "code" in params
    assert params["state"] == login_session.state

    authorization_code_repository = AuthorizationCodeRepository(session)
    code = params["code"]
    code_hash = get_token_hash(code)

    authorization_code = await authorization_code_repository.get_by_code(code_hash)
    assert authorization_code is not None
    assert authorization_code.nonce == login_session.nonce
    assert authorization_code.code_challenge == login_session.code_challenge
    assert (
        authorization_code.code_challenge_method == login_session.code_challenge_method
    )

    assert authorization_code.authenticated_at.timestamp() == pytest.approx(
        session_token.created_at.timestamp()
    )

    assert authorization_code.c_hash == get_validation_hash(code)

    assert authorization_code.acr == login_session.acr

    if login_session.response_type in ["code token", "code id_token token"]:
        assert "access_token" in params
        assert "token_type" in params
        assert params["token_type"] == "bearer"
        assert "refresh_token" not in params

        user = session_token.user
        tenant = user.tenant
        await access_token_assertions(
            access_token=params["access_token"],
            jwk=tenant.get_sign_jwk(),
            user=user,
            authenticated_at=authorization_code.authenticated_at,
            acr=authorization_code.acr,
        )

    if login_session.response_type in ["code id_token", "code id_token token"]:
        assert "id_token" in params
        tenant = session_token.user.tenant
        await id_token_assertions(
            id_token=params["id_token"],
            jwk=tenant.get_sign_jwk(),
            authenticated_at=authorization_code.authenticated_at,
            acr=authorization_code.acr,
            authorization_code_tuple=(authorization_code, code),
            access_token=params.get("access_token"),
        )


async def email_verification_requested_assertions(
    *,
    user: User,
    email: str,
    send_task_mock: MagicMock,
    session: AsyncSession,
):
    email_verification_repository = EmailVerificationRepository(session)
    email_verifications = await email_verification_repository.get_by_user(user.id)
    assert len(email_verifications) == 1
    email_verification = email_verifications[0]
    assert email_verification.email == email

    send_task_mock.assert_called_once()
    assert send_task_mock.call_args[0][0] == on_email_verification_requested
    assert send_task_mock.call_args[0][1] == str(email_verification.id)
    assert (
        get_verify_code_hash(send_task_mock.call_args[0][2]) == email_verification.code
    )
