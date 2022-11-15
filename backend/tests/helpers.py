import json
from datetime import datetime

from furl import furl
from jwcrypto import jwk, jwt

from fief.crypto.id_token import get_validation_hash
from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.models import AuthorizationCode, LoginSession, SessionToken, User
from fief.repositories import AuthorizationCodeRepository


async def access_token_assertions(*, access_token: str, jwk: jwk.JWK, user: User):
    access_token_jwt = jwt.JWT(jwt=access_token, algs=["RS256"], key=jwk)
    access_token_claims = json.loads(access_token_jwt.claims)

    assert access_token_claims["sub"] == str(user.id)
    assert "scope" in access_token_claims
    assert "permissions" in access_token_claims


async def id_token_assertions(
    *,
    id_token: str,
    jwk: jwk.JWK,
    authenticated_at: datetime,
    authorization_code_tuple: tuple[AuthorizationCode, str] | None = None,
    access_token: str | None = None,
):
    id_token_jwt = jwt.JWT(jwt=id_token, algs=["RS256"], key=jwk)
    id_token_claims = json.loads(id_token_jwt.claims)

    id_token_claims["auth_time"] == int(authenticated_at.timestamp())

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

    assert authorization_code.authenticated_at.replace(
        microsecond=0
    ) == session_token.created_at.replace(microsecond=0)

    assert authorization_code.c_hash == get_validation_hash(code)

    if login_session.response_type in ["code token", "code id_token token"]:
        assert "access_token" in params
        assert "token_type" in params
        assert params["token_type"] == "bearer"
        assert "refresh_token" not in params

        user = session_token.user
        tenant = user.tenant
        await access_token_assertions(
            access_token=params["access_token"], jwk=tenant.get_sign_jwk(), user=user
        )

    if login_session.response_type in ["code id_token", "code id_token token"]:
        assert "id_token" in params
        tenant = session_token.user.tenant
        await id_token_assertions(
            id_token=params["id_token"],
            jwk=tenant.get_sign_jwk(),
            authenticated_at=authorization_code.authenticated_at,
            authorization_code_tuple=(authorization_code, code),
            access_token=params.get("access_token"),
        )
