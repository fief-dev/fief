import json
import uuid
from datetime import datetime, timezone
from typing import List

from jwcrypto import jwk, jwt
from jwcrypto.common import JWException
from pydantic import UUID4

from fief.models import Client, User


class InvalidAccessToken(Exception):
    pass


def generate_access_token(
    key: jwk.JWK,
    host: str,
    client: Client,
    user: User,
    scope: List[str],
    permissions: List[str],
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
        "azp": client.client_id,
        "scope": " ".join(scope),
        "permissions": permissions,
    }

    token = jwt.JWT(header={"alg": "RS256"}, claims=claims)
    token.make_signed_token(key)

    return token.serialize()


def read_access_token(key: jwk.JWK, token: str) -> UUID4:
    try:
        decoded_jwt = jwt.JWT(jwt=token, key=key)
        claims = json.loads(decoded_jwt.claims)
        user_id = claims["sub"]
    except (JWException, KeyError, ValueError) as e:
        raise InvalidAccessToken() from e
    else:
        return uuid.UUID(user_id)
