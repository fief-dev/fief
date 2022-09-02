from typing import Optional, Type

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from fastapi_users.router import ErrorCode

from fief.apps.auth.forms.base import FormHelper
from fief.apps.auth.forms.register import (
    FRF,
    RF,
    get_finalize_register_form_class,
    get_register_form_class,
)
from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.register import (
    get_optional_registration_session,
    get_registration_flow,
    get_registration_session,
)
from fief.dependencies.tenant import get_current_tenant
from fief.locale import gettext_lazy as _
from fief.models import RegistrationSession, Tenant
from fief.services.authentication_flow import AuthenticationFlow
from fief.services.registration_flow import RegistrationFlow

router = APIRouter()


@router.api_route(
    "/register",
    methods=["GET", "POST"],
    name="register:register",
    dependencies=[Depends(get_login_session)],
)
async def register(
    request: Request,
    register_form_class: Type[RF] = Depends(get_register_form_class),
    registration_flow: RegistrationFlow = Depends(get_registration_flow),
    registration_session: Optional[RegistrationSession] = Depends(
        get_optional_registration_session
    ),
    tenant: Tenant = Depends(get_current_tenant),
):
    response: Response
    form_helper = FormHelper(
        register_form_class,
        "register.html",
        request=request,
        context={"tenant": tenant},
    )
    form = await form_helper.get_form()

    if registration_session is not None and await form_helper.is_submitted_and_valid():
        try:
            await registration_flow.create_user(
                form.data, tenant, registration_session, request=request
            )
        except UserAlreadyExists:
            return await form_helper.get_error_response(
                _("A user with the same email address already exists."),
                error_code=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
            )
        except InvalidPasswordException as e:
            form.password.errors.append(e.reason)
            return await form_helper.get_error_response(e.reason, "invalid_password")
        else:
            return RedirectResponse(
                tenant.url_path_for(request, "register:finalize"),
                status_code=status.HTTP_302_FOUND,
            )

    response = await form_helper.get_response()
    if registration_session is None:
        await registration_flow.create_registration_session(response, tenant=tenant)
    return response


@router.api_route(
    "/finalize",
    methods=["GET", "POST"],
    name="register:finalize",
    dependencies=[Depends(get_login_session)],
)
async def finalize(
    request: Request,
    finalize_register_form_class: Type[FRF] = Depends(get_finalize_register_form_class),
    registration_session: RegistrationSession = Depends(get_registration_session),
    registration_flow: RegistrationFlow = Depends(get_registration_flow),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    tenant: Tenant = Depends(get_current_tenant),
):
    form_helper = FormHelper(
        finalize_register_form_class,
        "finalize.html",
        request=request,
        context={"tenant": tenant},
    )
    form = await form_helper.get_form()

    user = registration_session.user
    if user is None and await form_helper.is_submitted_and_valid():
        try:
            user = await registration_flow.create_user(
                form.data, tenant, registration_session, request=request
            )
        except UserAlreadyExists:
            return await form_helper.get_error_response(
                _("A user with the same email address already exists."),
                error_code=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
            )
    # Prefill e-mail from OAuth account if available
    elif registration_session.oauth_account is not None:
        form.email.data = registration_session.oauth_account.account_email

    if user is not None:
        response = RedirectResponse(
            tenant.url_path_for(request, "auth:consent"),
            status_code=status.HTTP_302_FOUND,
        )
        response = await authentication_flow.create_session_token(response, user.id)
        response = await registration_flow.delete_registration_session(
            response, registration_session
        )
        return response

    return await form_helper.get_response()
