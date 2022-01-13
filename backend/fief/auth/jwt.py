from datetime import datetime, timezone
from typing import Optional

from fastapi_users.authentication.strategy import Strategy
from fastapi_users.authentication.strategy.base import StrategyDestroyNotSupportedError
from fastapi_users.manager import BaseUserManager, UserNotExists
from jwcrypto import jwk, jwt
from jwcrypto.common import JWException
from pydantic import UUID4

from fief.models import Account
from fief.schemas.user import UserCreate, UserDB


class AssymetricJWTStrategy(Strategy):
    """
    Authentication strategy issuing a signed JWT with assymetric algorithm.
    """

    def __init__(self, key: jwk.JWK, account: Account, lifetime_seconds: int) -> None:
        self.key = key
        self.account = account
        self.lifetime_seconds = lifetime_seconds

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[UserCreate, UserDB]
    ) -> Optional[UserDB]:
        try:
            decoded_jwt = jwt.JWT(jwt=token, key=self.key)
        except JWException:
            return None

        try:
            user_id = decoded_jwt.claims["sub"]
        except KeyError:
            return None

        try:
            user_uuid = UUID4(user_id)
        except ValueError:
            return None
        except UserNotExists:
            return None
        else:
            return await user_manager.get(user_uuid)

    async def write_token(self, user: UserDB) -> str:
        iat = int(datetime.now(timezone.utc).timestamp())
        exp = iat + self.lifetime_seconds

        claims = {
            "iss": f"https://{self.account.domain}",
            "sub": str(user.id),
            "aud": [str(user.tenant_id)],
            "exp": exp,
            "iat": iat,
            # "azp": "client_id",
        }

        token = jwt.JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(self.key)

        return token.serialize()

    async def destroy_token(self, token: str, user: UserDB) -> None:
        raise StrategyDestroyNotSupportedError()
