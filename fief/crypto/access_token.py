import json
from datetime import datetime, timezone
from typing import Any

from jwcrypto import jwk, jwt
from jwcrypto.common import JWException

from fief.models import Client, User
from fief.services.acr import ACR


class InvalidAccessToken(Exception):
    pass


def generate_access_token(
    key: jwk.JWK,
    host: str,
    client: Client,
    authenticated_at: datetime,
    acr: ACR,
    user: User,
    scope: list[str],
    permissions: list[str],
    lifetime_seconds: int,
) -> str:
    iat = int(datetime.now(timezone.utc).timestamp())
    exp = iat + lifetime_seconds

    claims = {
        "iss": host,
        "sub": str(user.id),
        "aud": [client.client_id],
        "exp": exp,
        "iat": iat,
        "auth_time": int(authenticated_at.timestamp()),
        "acr": str(acr),
        "azp": client.client_id,
        "scope": " ".join(scope),
        "permissions": permissions,
    }

    token = jwt.JWT(header={"alg": "RS256", "kid": key["kid"]}, claims=claims)
    token.make_signed_token(key)

    return token.serialize()


def read_access_token(key: jwk.JWK, token: str) -> dict[str, Any]:
    try:
        decoded_jwt = jwt.JWT(jwt=token, key=key)
        return json.loads(decoded_jwt.claims)
    except JWException as e:
        raise InvalidAccessToken() from e
