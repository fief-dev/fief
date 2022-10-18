from typing import List, Optional

from fief.locale import gettext_lazy as _
from fief.models import OAuthProvider, Tenant
from fief.schemas.auth import (
    AuthorizeError,
    AuthorizeRedirectError,
    LoginError,
    LogoutError,
    TokenError,
)
from fief.schemas.oauth import OAuthError


class AuthorizeException(Exception):
    def __init__(self, error: AuthorizeError, tenant: Optional[Tenant] = None) -> None:
        self.error = error
        self.tenant = tenant


class AuthorizeRedirectException(Exception):
    def __init__(
        self,
        error: AuthorizeRedirectError,
        redirect_uri: str,
        response_mode: str,
        state: Optional[str],
        tenant: Optional[Tenant] = None,
    ) -> None:
        self.error = error
        self.redirect_uri = redirect_uri
        self.response_mode = response_mode
        self.state = state
        self.tenant = tenant


class LoginException(Exception):
    def __init__(
        self,
        error: LoginError,
        oauth_providers: Optional[List[OAuthProvider]] = None,
        tenant: Optional[Tenant] = None,
        *,
        fatal: bool = False
    ) -> None:
        self.error = error
        self.oauth_providers = oauth_providers
        self.tenant = tenant
        self.fatal = fatal


class OAuthException(Exception):
    def __init__(
        self,
        error: OAuthError,
        oauth_providers: Optional[List[OAuthProvider]] = None,
        tenant: Optional[Tenant] = None,
        *,
        fatal: bool = False
    ) -> None:
        self.error = error
        self.oauth_providers = oauth_providers
        self.tenant = tenant
        self.fatal = fatal


class TokenRequestException(Exception):
    def __init__(self, error: TokenError) -> None:
        self.error = error


class LogoutException(Exception):
    def __init__(self, error: LogoutError, tenant: Optional[Tenant] = None) -> None:
        self.error = error
        self.tenant = tenant
