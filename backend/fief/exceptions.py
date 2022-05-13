from gettext import gettext as _
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError
from starlette.requests import FormData

from fief.locale import Translations
from fief.models import Client, Tenant
from fief.schemas.auth import (
    AuthorizeError,
    AuthorizeRedirectError,
    ConsentError,
    LoginError,
    LogoutError,
    TokenError,
)
from fief.schemas.register import RegisterError
from fief.schemas.reset import ResetPasswordError

PYDANTIC_ERROR_MESSAGES = {
    "value_error.missing": _("This field is required."),
    "value_error.any_str.min_length": _("This field is required."),
    "value_error.email": _("This email address is invalid."),
    "value_error.date": _("This date is invalid."),
    "value_error.datetime": _("This date and time is invalid."),
    "value_error.phone_number.invalid": _("This phone number is invalid."),
    "value_error.phone_number.missing_region": _("The country code is missing."),
    "value_error.country_code.invalid": _("This country code is invalid."),
    "value_error.timezone.invalid": _("This timezone is invalid."),
    "value_error.boolean.must_be_true": _("This must be checked."),
    "type_error.bool": _("This value is invalid."),
    "type_error.integer": _("This value is invalid."),
    "type_error.enum": _("This value is invalid."),
}


class FormValidationError(ValidationError):
    def __init__(
        self,
        template: str,
        context: Dict[str, Any],
        translations: Translations,
        *args,
        **kwargs,
    ) -> None:
        self.template = template
        self.context = context
        self.translations = translations
        super().__init__(*args, **kwargs)

    def form_errors(self) -> Dict[Union[str, int], Any]:
        form_errors: Dict[Union[str, int], Any] = {}
        for error in self.errors():
            error_dict = form_errors
            for key in error["loc"][:-1]:
                error_dict = error_dict.setdefault(key, {})
            error_dict[error["loc"][-1]] = self.translations.gettext(
                PYDANTIC_ERROR_MESSAGES[error["type"]]
            )
        return form_errors


class RegisterException(Exception):
    def __init__(
        self,
        error: RegisterError,
        context: Dict[str, Any],
        form_data: Optional[Dict[str, Any]] = None,
        *,
        fatal: bool = False,
    ) -> None:
        self.error = error
        self.context = context
        self.form_data = form_data
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


class LogoutException(Exception):
    def __init__(self, error: LogoutError, tenant: Optional[Tenant] = None) -> None:
        self.error = error
        self.tenant = tenant
