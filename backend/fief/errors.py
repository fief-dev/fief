from enum import Enum
from gettext import gettext as _
from typing import Dict, List, Optional, Union

from pydantic import ValidationError
from starlette.requests import FormData

from fief.locale import Translations
from fief.models import Client, Tenant
from fief.schemas.auth import (
    AuthorizeError,
    AuthorizeRedirectError,
    ConsentError,
    LoginError,
    TokenError,
)
from fief.schemas.register import RegisterError
from fief.schemas.reset import ResetPasswordError


class APIErrorCode(str, Enum):
    CSRF_CHECK_FAILED = "CSRF_CHECK_FAILED"
    ACCOUNT_CREATE_MISSING_DATABASE_SETTINGS = (
        "ACCOUNT_CREATE_MISSING_DATABASE_SETTINGS"
    )
    ACCOUNT_DB_CONNECTION_ERROR = "ACCOUNT_DB_CONNECTION_ERROR"


PYDANTIC_ERROR_MESSAGES = {
    "value_error.missing": _("This field is required."),
    "value_error.email": _("This email address is invalid."),
}


class FormValidationError(ValidationError):
    def __init__(
        self, template: str, tenant: Tenant, translations: Translations, *args, **kwargs
    ) -> None:
        self.template = template
        self.tenant = tenant
        self.translations = translations
        super().__init__(*args, **kwargs)

    def form_errors(self) -> Dict[Union[str, int], str]:
        form_errors = {}
        for error in self.errors():
            form_errors[error["loc"][0]] = self.translations.gettext(
                PYDANTIC_ERROR_MESSAGES[error["type"]]
            )
        return form_errors


class RegisterException(Exception):
    def __init__(
        self,
        error: RegisterError,
        form_data: Optional[FormData] = None,
        tenant: Optional[Tenant] = None,
        *,
        fatal: bool = False,
    ) -> None:
        self.error = error
        self.form_data = form_data
        self.tenant = tenant
        self.fatal = fatal


class AuthorizeException(Exception):
    def __init__(self, error: AuthorizeError, tenant: Optional[Tenant] = None) -> None:
        self.error = error
        self.tenant = tenant


class AuthorizeRedirectException(Exception):
    def __init__(
        self,
        error: AuthorizeRedirectError,
        redirect_uri: str,
        state: Optional[str],
        tenant: Optional[Tenant] = None,
    ) -> None:
        self.error = error
        self.redirect_uri = redirect_uri
        self.state = state
        self.tenant = tenant


class LoginException(Exception):
    def __init__(
        self, error: LoginError, tenant: Optional[Tenant] = None, *, fatal: bool = False
    ) -> None:
        self.error = error
        self.tenant = tenant
        self.fatal = fatal


class ConsentException(Exception):
    def __init__(
        self,
        error: ConsentError,
        client: Client,
        scope: List[str],
        tenant: Optional[Tenant] = None,
        *,
        fatal: bool = False,
    ) -> None:
        self.error = error
        self.client = client
        self.scope = scope
        self.tenant = tenant
        self.fatal = fatal


class TokenRequestException(Exception):
    def __init__(self, error: TokenError) -> None:
        self.error = error


class ResetPasswordException(Exception):
    def __init__(
        self,
        error: ResetPasswordError,
        form_data: Optional[FormData] = None,
        tenant: Optional[Tenant] = None,
        *,
        fatal: bool = False,
    ) -> None:
        self.error = error
        self.form_data = form_data
        self.tenant = tenant
        self.fatal = fatal
