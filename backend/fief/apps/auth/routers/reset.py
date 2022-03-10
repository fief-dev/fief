from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi_users.manager import (
    InvalidPasswordException,
    InvalidResetPasswordToken,
    UserInactive,
    UserNotExists,
)

from fief.apps.auth.templates import templates
from fief.csrf import check_csrf
from fief.dependencies.auth import get_optional_login_session
from fief.dependencies.locale import Translations, get_gettext, get_translations
from fief.dependencies.reset import (
    get_forgot_password_request,
    get_reset_password_request,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.exceptions import ResetPasswordException
from fief.models import LoginSession, Tenant
from fief.schemas.reset import (
    ForgotPasswordRequest,
    ResetPasswordError,
    ResetPasswordRequest,
)

router = APIRouter(dependencies=[Depends(check_csrf), Depends(get_translations)])


@router.get("/forgot", name="reset:forgot.get")
async def get_forgot_password(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
):
    return templates.LocaleTemplateResponse(
        "forgot_password.html",
        {"request": request, "tenant": tenant},
        translations=translations,
    )


@router.post("/forgot", name="reset:forgot.post")
async def post_forgot_password(
    request: Request,
    forgot_password_request: ForgotPasswordRequest = Depends(
        get_forgot_password_request
    ),
    user_manager: UserManager = Depends(get_user_manager),
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
):
    try:
        user = await user_manager.get_by_email(forgot_password_request.email)
        await user_manager.forgot_password(user, request)
    except (UserNotExists, UserInactive):
        pass

    success = translations.gettext(
        "Check your inbox! If an account associated with this email address exists in our system, you'll receive a link to reset your password."
    )

    return templates.LocaleTemplateResponse(
        "forgot_password.html",
        {"request": request, "tenant": tenant, "success": success},
        translations=translations,
    )


@router.get("/reset", name="reset:reset.get")
async def get_reset_password(
    request: Request,
    token: Optional[str] = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
    _=Depends(get_gettext),
):
    if token is None:
        raise ResetPasswordException(
            ResetPasswordError.get_missing_token(
                _("The reset password token is missing.")
            ),
            tenant=tenant,
            fatal=True,
        )

    return templates.LocaleTemplateResponse(
        "reset_password.html",
        {"request": request, "tenant": tenant, "token": token},
        translations=translations,
    )


@router.post("/reset", name="reset:reset.post")
async def post_reset_password(
    request: Request,
    reset_password_request: ResetPasswordRequest = Depends(get_reset_password_request),
    user_manager: UserManager = Depends(get_user_manager),
    login_session: Optional[LoginSession] = Depends(get_optional_login_session),
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
    _=Depends(get_gettext),
):
    try:
        await user_manager.reset_password(
            reset_password_request.token, reset_password_request.password, request
        )
    except (InvalidResetPasswordToken, UserNotExists, UserInactive) as e:
        raise ResetPasswordException(
            ResetPasswordError.get_invalid_token(
                _("The reset password token is invalid or expired.")
            ),
            tenant=tenant,
            fatal=True,
        ) from e
    except InvalidPasswordException as e:
        raise ResetPasswordException(
            ResetPasswordError.get_invalid_password(e.reason),
            form_data=await request.form(),
            tenant=tenant,
        ) from e

    if login_session is not None:
        redirection = tenant.url_for(request, "auth:login.get")
        return RedirectResponse(url=redirection, status_code=status.HTTP_302_FOUND)

    return templates.LocaleTemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "tenant": tenant,
            "success": _("Your password has been changed!"),
        },
        translations=translations,
    )
