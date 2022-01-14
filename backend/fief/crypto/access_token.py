import uuid
from datetime import datetime, timezone

from jwcrypto import jwk, jwt
from jwcrypto.common import JWException
from pydantic import UUID4

from fief.models import Account, Client
from fief.schemas.user import UserDB


class InvalidAccessToken(Exception):
    pass


def generate_access_token(
    key: jwk.JWK, account: Account, client: Client, user: UserDB, lifetime_seconds: int
) -> str:
    iat = int(datetime.now(timezone.utc).timestamp())
    exp = iat + lifetime_seconds

    claims = {
        "iss": f"https://{account.domain}",
        "sub": str(user.id),
        "aud": [client.client_id],
        "exp": exp,
        "iat": iat,
        "azp": client.client_id,
    }

    token = jwt.JWT(header={"alg": "RS256"}, claims=claims)
    token.make_signed_token(key)

    return token.serialize()


def read_access_token(key: jwk.JWK, token: str) -> UUID4:
    try:
        decoded_jwt = jwt.JWT(jwt=token, key=key)
        user_id = decoded_jwt.claims["sub"]
    except JWException as e:
        raise InvalidAccessToken() from e
    except KeyError as e:
        raise InvalidAccessToken() from e
    else:
        return uuid.UUID(user_id)
