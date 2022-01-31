from enum import Enum
from typing import Optional

from fief.models import Tenant
from fief.schemas.auth import AuthorizeError, LoginError, TokenError


class ErrorCode(str, Enum):
    ACCOUNT_DB_CONNECTION_ERROR = "ACCOUNT_DB_CONNECTION_ERROR"
    AUTH_INVALID_CLIENT_ID = "AUTH_INVALID_CLIENT_ID"


class AuthorizeException(Exception):
    def __init__(self, error: AuthorizeError, tenant: Optional[Tenant] = None) -> None:
        self.error = error
        self.tenant = tenant


class LoginException(Exception):
    def __init__(
        self, error: LoginError, tenant: Optional[Tenant] = None, *, fatal: bool = False
    ) -> None:
        self.error = error
        self.tenant = tenant
        self.fatal = fatal


class TokenRequestException(Exception):
    def __init__(self, error: TokenError) -> None:
        self.error = error
