from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from fastapi_users.router import ErrorCode

from fief.apps.auth.forms.base import FormHelper
from fief.apps.auth.forms.register import RF, get_register_form_class
from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.register import (
    get_optional_registration_session,
    get_registration_flow,
)
from fief.dependencies.tenant import get_current_tenant
from fief.exceptions import LoginException
from fief.locale import gettext_lazy as _
from fief.models import (
    OAuthProvider,
    RegistrationSession,
    RegistrationSessionFlow,
    Tenant,
)
from fief.schemas.auth import LoginError
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
    register_form_class: type[RF] = Depends(get_register_form_class),
    registration_flow: RegistrationFlow = Depends(get_registration_flow),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    registration_session: RegistrationSession
    | None = Depends(get_optional_registration_session),
    oauth_providers: list[OAuthProvider] | None = Depends(get_oauth_providers),
    tenant: Tenant = Depends(get_current_tenant),
):
    if not tenant.registration_allowed:
        raise LoginException(
            LoginError.get_registration_disabled(_("Registration is disabled")),
            fatal=True,
        )

    response: Response
    form_helper = FormHelper(
        register_form_class,
        "register.html",
        request=request,
        context={
            "finalize": registration_session is not None
            and registration_session.flow != RegistrationSessionFlow.PASSWORD,
            "oauth_providers": oauth_providers,
            "tenant": tenant,
        },
    )
    form = await form_helper.get_form()

    if (
        request.method != "POST"
        and registration_session is not None
        and registration_session.email
    ):
        form.email.data = registration_session.email

    if registration_session is not None and await form_helper.is_submitted_and_valid():
        try:
            user = await registration_flow.create_user(
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
            response = RedirectResponse(
                tenant.url_path_for(request, "auth:consent"),
                status_code=status.HTTP_302_FOUND,
            )
            response = await authentication_flow.create_session_token(response, user.id)
            response = await registration_flow.delete_registration_session(
                response, registration_session
            )
            return response

    response = await form_helper.get_response()
    if registration_session is None:
        await registration_flow.create_registration_session(
            response, flow=RegistrationSessionFlow.PASSWORD, tenant=tenant
        )
    return response
