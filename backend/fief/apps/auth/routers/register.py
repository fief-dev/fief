from typing import Any, Dict, List, Type

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists

from fief.apps.auth.templates import templates
from fief.csrf import check_csrf
from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.form import get_form_data_dict
from fief.dependencies.locale import Translations, get_gettext, get_translations
from fief.dependencies.register import get_register_context, get_user_create
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.user_field import get_user_create_internal_model, get_user_fields
from fief.dependencies.users import UserManager, get_user_manager
from fief.exceptions import RegisterException
from fief.models import Tenant, UserField
from fief.schemas.register import RegisterError
from fief.schemas.user import UF, UserCreate, UserCreateInternal
from fief.services.authentication_flow import AuthenticationFlow

router = APIRouter(dependencies=[Depends(check_csrf), Depends(get_translations)])


@router.get("/register", name="register:get", dependencies=[Depends(get_login_session)])
async def get_register(
    request: Request,
    register_context: Dict[str, Any] = Depends(get_register_context),
    translations: Translations = Depends(get_translations),
):
    return templates.LocaleTemplateResponse(
        "register.html",
        {
            "request": request,
            **register_context,
        },
        translations=translations,
    )


@router.post(
    "/register", name="register:post", dependencies=[Depends(get_login_session)]
)
async def post_register(
    request: Request,
    user: UserCreate[UF] = Depends(get_user_create),
    form_data_dict: Dict[str, Any] = Depends(get_form_data_dict),
    user_create_internal_model: Type[UserCreateInternal[UF]] = Depends(
        get_user_create_internal_model
    ),
    user_manager: UserManager = Depends(get_user_manager),
    user_fields: List[UserField] = Depends(get_user_fields),
    register_context: Dict[str, Any] = Depends(get_register_context),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    _=Depends(get_gettext),
):
    try:
        user_create = user_create_internal_model(
            **user.dict(), fields=user.fields, tenant_id=tenant.id
        )
        created_user = await user_manager.create_with_fields(
            user_create,
            user_fields=user_fields,
            safe=True,
            request=request,
        )
    except UserAlreadyExists as e:
        raise RegisterException(
            RegisterError.get_user_already_exists(
                _("A user with the same email address already exists.")
            ),
            context=register_context,
            form_data=form_data_dict,
        ) from e
    except InvalidPasswordException as e:
        raise RegisterException(
            RegisterError.get_invalid_password(e.reason),
            context=register_context,
            form_data=form_data_dict,
        ) from e

    response = RedirectResponse(
        tenant.url_for(request, "auth:consent.get"),
        status_code=status.HTTP_302_FOUND,
    )
    response = await authentication_flow.create_session_token(response, created_user.id)

    return response
