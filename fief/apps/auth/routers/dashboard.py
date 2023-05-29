from typing import TypedDict

from fastapi import APIRouter, Depends, Header, Request
from fastapi_users.exceptions import UserAlreadyExists

from fief import schemas
from fief.apps.auth.forms.password import ChangePasswordForm
from fief.apps.auth.forms.profile import PF, get_profile_form_class
from fief.dependencies.branding import get_show_branding
from fief.dependencies.session_token import get_user_from_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.theme import get_current_theme
from fief.dependencies.user_field import get_user_fields
from fief.dependencies.users import UserManager, get_user_manager, get_user_update_model
from fief.forms import FormHelper
from fief.locale import gettext_lazy as _
from fief.models import Tenant, Theme, User, UserField

router = APIRouter()


class BaseContext(TypedDict):
    request: Request
    user: User
    tenant: Tenant
    theme: Theme
    show_branding: bool


async def get_base_context(
    request: Request,
    user: User = Depends(get_user_from_session_token),
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
    user: User = Depends(get_user_from_session_token),
    user_manager: UserManager = Depends(get_user_manager),
    profile_form_class: type[PF] = Depends(get_profile_form_class),
    user_update_model: type[schemas.user.UserUpdate[schemas.user.UF]] = Depends(
        get_user_update_model
    ),
    user_fields: list[UserField] = Depends(get_user_fields),
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

        try:
            user = await user_manager.update_with_fields(
                user_update, user, user_fields=user_fields, request=request
            )
        except UserAlreadyExists:
            message = _("A user with this email address already exists.")
            form.email.errors.append(message)
            return await form_helper.get_error_response(message, "user_already_exists")

        form_helper.context["success"] = _(
            "Your profile has successfully been updated."
        )

    return await form_helper.get_response()


@router.api_route("/password", methods=["GET", "POST"], name="auth.dashboard:password")
async def update_password(
    request: Request,
    hx_trigger: str | None = Header(None),
    user: User = Depends(get_user_from_session_token),
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

        await user_manager._update(user, {"password": new_password})

        form_helper.context["success"] = _(
            "Your password has been changed successfully."
        )

    return await form_helper.get_response()
