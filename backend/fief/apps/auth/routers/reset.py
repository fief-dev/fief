from fastapi import APIRouter, Depends, Request
from fastapi_users.manager import UserInactive, UserNotExists

from fief.apps.auth.templates import templates
from fief.csrf import check_csrf
from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.locale import Translations, get_gettext, get_translations
from fief.dependencies.register import get_user_create
from fief.dependencies.reset import get_forgot_password_request
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import RegisterException
from fief.models import Tenant
from fief.schemas.reset import ForgotPasswordRequest
from fief.schemas.user import UserCreate
from fief.services.authentication_flow import AuthenticationFlow

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
    except UserNotExists:
        pass
    except UserInactive:
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
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
):
    return templates.LocaleTemplateResponse(
        "forgot_password.html",
        {"request": request, "tenant": tenant},
        translations=translations,
    )
