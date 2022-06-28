from typing import List, Type

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from fastapi_users.router import ErrorCode

from fief.apps.auth.forms.base import FormHelper
from fief.apps.auth.forms.register import RF, get_register_form_class
from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.user_field import get_user_create_internal_model, get_user_fields
from fief.dependencies.users import UserManager, get_user_manager
from fief.locale import gettext_lazy as _
from fief.models import Tenant, UserField
from fief.schemas.user import UF, UserCreateInternal
from fief.services.authentication_flow import AuthenticationFlow

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
    user_create_internal_model: Type[UserCreateInternal[UF]] = Depends(
        get_user_create_internal_model
    ),
    user_manager: UserManager = Depends(get_user_manager),
    user_fields: List[UserField] = Depends(get_user_fields),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
):
    form_helper = FormHelper(
        register_form_class,
        "register.html",
        request=request,
        context={"tenant": tenant},
    )
    form = await form_helper.get_form()

    if await form_helper.is_submitted_and_valid():
        try:
            user_create = user_create_internal_model(**form.data, tenant_id=tenant.id)
            created_user = await user_manager.create_with_fields(
                user_create,
                user_fields=user_fields,
                safe=True,
                request=request,
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
            response = await authentication_flow.create_session_token(
                response, created_user.id
            )

            return response

    return await form_helper.get_response()
