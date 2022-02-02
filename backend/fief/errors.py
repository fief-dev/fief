from enum import Enum
from gettext import gettext as _
from typing import Dict, Optional, Union

from pydantic import ValidationError
from starlette.requests import FormData

from fief.models import Tenant
from fief.schemas.auth import AuthorizeError, LoginError, TokenError
from fief.schemas.register import RegisterError


class APIErrorCode(str, Enum):
    ACCOUNT_DB_CONNECTION_ERROR = "ACCOUNT_DB_CONNECTION_ERROR"


PYDANTIC_ERROR_MESSAGES = {
    "value_error.missing": _("This field is required."),
    "value_error.email": _("This email address is invalid."),
}


class FormValidationError(ValidationError):
    def __init__(self, template: str, tenant: Tenant, *args, **kwargs) -> None:
        self.template = template
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def form_errors(self) -> Dict[Union[str, int], str]:
        form_errors = {}
        for error in self.errors():
            form_errors[error["loc"][0]] = PYDANTIC_ERROR_MESSAGES[error["type"]]
        return form_errors


class RegisterException(Exception):
    def __init__(
        self,
        error: RegisterError,
        form_data: Optional[FormData] = None,
        tenant: Optional[Tenant] = None,
    ) -> None:
        self.error = error
        self.form_data = form_data
        self.tenant = tenant


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
