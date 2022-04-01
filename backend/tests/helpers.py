import json
from datetime import datetime
from typing import Optional

from furl import furl
from jwcrypto import jwk, jwt

from fief.crypto.token import get_token_hash
from fief.db import AsyncSession
from fief.managers import AuthorizationCodeManager
from fief.models import AuthorizationCode, LoginSession, SessionToken


async def id_token_assertions(
    *,
    id_token: str,
    jwk: jwk.JWK,
    authenticated_at: datetime,
    authorization_code: Optional[AuthorizationCode] = None,
    access_token: Optional[str] = None,
):
    id_token_jwt = jwt.JWT(jwt=id_token, algs=["RS256"], key=jwk)
    id_token_claims = json.loads(id_token_jwt.claims)

    id_token_claims["auth_time"] == int(authenticated_at.timestamp())

    if authorization_code is not None:
        if authorization_code.nonce is not None:
            assert id_token_claims["nonce"] == authorization_code.nonce
        else:
            assert "nonce" not in id_token_claims
        assert "c_hash" in id_token_claims

    if access_token is not None:
        assert "at_hash" in id_token_claims


async def authorization_code_assertions(
    *,
    redirect_uri: str,
    login_session: LoginSession,
    session_token: SessionToken,
    session: AsyncSession,
):
    assert redirect_uri.startswith(login_session.redirect_uri)
    parsed_location = furl(redirect_uri)
    query_params = parsed_location.query.params
    assert "code" in query_params
    assert query_params["state"] == login_session.state

    authorization_code_manager = AuthorizationCodeManager(session)
    code_hash = get_token_hash(query_params["code"])

    authorization_code = await authorization_code_manager.get_by_code(code_hash)
    assert authorization_code is not None
    assert authorization_code.nonce == login_session.nonce
    assert authorization_code.code_challenge == login_session.code_challenge
    assert (
        authorization_code.code_challenge_method == login_session.code_challenge_method
    )

    assert authorization_code.authenticated_at.replace(
        microsecond=0
    ) == session_token.created_at.replace(microsecond=0)

    if login_session.response_type in ["code token", "code id_token token"]:
        assert "access_token" in query_params
        assert "token_type" in query_params
        assert query_params["token_type"] == "bearer"
        assert "refresh_token" not in query_params

    if login_session.response_type in ["code id_token", "code id_token token"]:
        assert "id_token" in query_params
        tenant = session_token.user.tenant
        await id_token_assertions(
            id_token=query_params["id_token"],
            jwk=tenant.get_sign_jwk(),
            authenticated_at=authorization_code.authenticated_at,
            authorization_code=authorization_code,
            access_token=query_params.get("access_token"),
        )
