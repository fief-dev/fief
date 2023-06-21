from typing import TypedDict

from fastapi import APIRouter, Depends, Header, Request, status

from fief import schemas
from fief.apps.auth.forms.password import ChangePasswordForm
from fief.apps.auth.forms.profile import PF, ChangeEmailForm, get_profile_form_class
from fief.apps.auth.forms.verify_email import VerifyEmailForm
from fief.apps.auth.responses import HXLocationResponse
from fief.dependencies.branding import get_show_branding
from fief.dependencies.session_token import (
    get_verified_email_user_from_session_token_or_verify,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.theme import get_current_theme
from fief.dependencies.users import get_user_manager, get_user_update_model
from fief.forms import FormHelper
from fief.locale import gettext_lazy as _
from fief.models import Tenant, Theme, User
from fief.services.user_manager import (
    InvalidEmailVerificationCodeError,
    UserAlreadyExistsError,
    UserManager,
)
from fief.settings import settings

router = APIRouter()


class BaseContext(TypedDict):
    request: Request
    user: User
    tenant: Tenant
    theme: Theme
    show_branding: bool


async def get_base_context(
    request: Request,
    user: User = Depends(get_verified_email_user_from_session_token_or_verify),
    tenant: Tenant = Depends(get_current_tenant),
    theme: Theme = Depends(get_current_theme),
    show_branding: bool = Depends(get_show_branding),
) -> BaseContext:
    return {
        "request": request,
        "user": user,
        "tenant": tenant,
        "theme": theme,
        "show_branding": show_branding,
    }


@router.api_route("/", methods=["GET", "POST"], name="auth.dashboard:profile")
async def update_profile(
    request: Request,
    user: User = Depends(get_verified_email_user_from_session_token_or_verify),
    user_manager: UserManager = Depends(get_user_manager),
    profile_form_class: type[PF] = Depends(get_profile_form_class),
    user_update_model: type[schemas.user.UserUpdate[schemas.user.UF]] = Depends(
        get_user_update_model
    ),
    context: BaseContext = Depends(get_base_context),
):
    form_helper = FormHelper(
        profile_form_class,
        "auth/dashboard/index.html",
        request=request,
        object=user,
        context={**context, "current_route": "auth.dashboard:profile"},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        data = form.data
        user_update = user_update_model(**data)

        user = await user_manager.update(user_update, user, request=request)

        form_helper.context["success"] = _(
            "Your profile has successfully been updated."
        )

    return await form_helper.get_response()


@router.api_route(
    "/email/change", methods=["GET", "POST"], name="auth.dashboard:email_change"
)
async def email_change(
    request: Request,
    user: User = Depends(get_verified_email_user_from_session_token_or_verify),
    user_manager: UserManager = Depends(get_user_manager),
    context: BaseContext = Depends(get_base_context),
    tenant: Tenant = Depends(get_current_tenant),
):
    form_helper = FormHelper(
        ChangeEmailForm,
        "auth/dashboard/email/change.html",
        request=request,
        object=user,
        context={**context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        current_password = form.current_password.data
        (
            current_password_valid,
            _hash_update,
        ) = user_manager.password_helper.verify_and_update(
            current_password, user.hashed_password
        )

        if not current_password_valid:
            message = _("Your password is invalid.")
            form.current_password.errors.append(message)
            return await form_helper.get_error_response(
                message, "invalid_current_password"
            )

        try:
            await user_manager.request_verify_email(
                user, form.email.data, request=request
            )
        except UserAlreadyExistsError:
            message = _("A user with this email address already exists.")
            form.email.errors.append(message)
            return await form_helper.get_error_response(message, "user_already_exists")

        return HXLocationResponse(
            tenant.url_for(request, "auth.dashboard:email_verify"),
            status_code=status.HTTP_202_ACCEPTED,
            hx_target="#email-change",
        )

    return await form_helper.get_response()


@router.api_route(
    "/email/verify", methods=["GET", "POST"], name="auth.dashboard:email_verify"
)
async def email_verify(
    request: Request,
    user: User = Depends(get_verified_email_user_from_session_token_or_verify),
    user_manager: UserManager = Depends(get_user_manager),
    context: BaseContext = Depends(get_base_context),
    tenant: Tenant = Depends(get_current_tenant),
):
    form_helper = FormHelper(
        VerifyEmailForm,
        "auth/dashboard/email/verify.html",
        request=request,
        object=user,
        context={**context, "code_length": settings.email_verification_code_length},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        try:
            user = await user_manager.verify_email(
                user, form.code.data, request=request
            )
        except InvalidEmailVerificationCodeError:
            return await form_helper.get_error_response(
                _(
                    "The verification code is invalid. Please check that you have entered it correctly. "
                    "If the code was copied and pasted, ensure it has not expired. "
                    "If it has been more than one hour, start over the email change process."
                ),
                "invalid_code",
            )

        return HXLocationResponse(
            tenant.url_for(request, "auth.dashboard:profile"),
        )

    return await form_helper.get_response()


@router.api_route("/password", methods=["GET", "POST"], name="auth.dashboard:password")
async def update_password(
    request: Request,
    hx_trigger: str | None = Header(None),
    user: User = Depends(get_verified_email_user_from_session_token_or_verify),
    user_manager: UserManager = Depends(get_user_manager),
    context: BaseContext = Depends(get_base_context),
):
    form_helper = FormHelper(
        ChangePasswordForm,
        "auth/dashboard/password.html",
        request=request,
        context={**context, "current_route": "auth.dashboard:password"},
    )

    if await form_helper.is_submitted_and_valid() and hx_trigger is None:
        form = await form_helper.get_form()

        old_password = form.old_password.data
        (
            old_password_valid,
            _hash_update,
        ) = user_manager.password_helper.verify_and_update(
            old_password, user.hashed_password
        )

        if not old_password_valid:
            message = _("Old password is invalid.")
            form.old_password.errors.append(message)
            return await form_helper.get_error_response(message, "invalid_old_password")

        new_password = form.new_password.data
        new_password_confirm = form.new_password_confirm.data

        if new_password != new_password_confirm:
            message = _("Passwords don't match.")
            form.new_password.errors.append(message)
            return await form_helper.get_error_response(message, "passwords_dont_match")

        user = await user_manager.set_user_attributes(user, password=new_password)
        await user_manager.user_repository.update(user)

        form_helper.context["success"] = _(
            "Your password has been changed successfully."
        )

    return await form_helper.get_response()
