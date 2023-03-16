from typing import TypedDict

from fastapi import APIRouter, Depends, Request
from fastapi_users.exceptions import InvalidPasswordException

from fief.apps.auth.forms.password import ChangePasswordForm
from fief.dependencies.session_token import get_user_from_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.theme import get_current_theme
from fief.dependencies.users import UserManager, get_user_manager
from fief.forms import FormHelper
from fief.locale import gettext_lazy as _
from fief.models import Tenant, Theme, User
from fief.templates import templates

router = APIRouter()


class BaseContext(TypedDict):
    request: Request
    user: User
    tenant: Tenant
    theme: Theme


async def get_base_context(
    request: Request,
    user: User = Depends(get_user_from_session_token),
    tenant: Tenant = Depends(get_current_tenant),
    theme: Theme = Depends(get_current_theme),
) -> BaseContext:
    return {"request": request, "user": user, "tenant": tenant, "theme": theme}


@router.get("/", name="auth.dashboard:index")
async def get_index(context: BaseContext = Depends(get_base_context)):
    return templates.TemplateResponse(
        "auth/dashboard/index.html",
        {**context, "current_route": "auth.dashboard.index"},
    )


@router.api_route("/password", methods=["GET", "POST"], name="auth.dashboard:password")
async def get_password(
    request: Request,
    user: User = Depends(get_user_from_session_token),
    user_manager: UserManager = Depends(get_user_manager),
    context: BaseContext = Depends(get_base_context),
):
    form_helper = FormHelper(
        ChangePasswordForm,
        "auth/dashboard/password.html",
        request=request,
        context={**context, "current_route": "auth.dashboard.password"},
    )

    if await form_helper.is_submitted_and_valid():
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

        try:
            await user_manager._update(user, {"password": new_password})
        except InvalidPasswordException as e:
            form.new_password.errors.append(e.reason)
            return await form_helper.get_error_response(e.reason, "invalid_password")

        form_helper.context["success"] = _(
            "Your password has been changed successfully."
        )

    return await form_helper.get_response()
