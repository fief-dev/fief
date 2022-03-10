from fastapi import Depends, Request
from pydantic import ValidationError

from fief.dependencies.locale import get_translations
from fief.dependencies.tenant import get_current_tenant
from fief.exceptions import FormValidationError
from fief.locale import Translations
from fief.models import Tenant
from fief.schemas.reset import ForgotPasswordRequest, ResetPasswordRequest


async def get_forgot_password_request(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
) -> ForgotPasswordRequest:
    form = await request.form()
    try:
        return ForgotPasswordRequest(**form)
    except ValidationError as e:
        raise FormValidationError(
            "forgot_password.html",
            tenant,
            translations,
            e.raw_errors,
            ForgotPasswordRequest,
        ) from e


async def get_reset_password_request(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
) -> ResetPasswordRequest:
    form = await request.form()
    try:
        return ResetPasswordRequest(**form)
    except ValidationError as e:
        raise FormValidationError(
            "reset_password.html",
            tenant,
            translations,
            e.raw_errors,
            ResetPasswordRequest,
        ) from e
