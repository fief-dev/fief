from typing import List, Optional, Type

from fastapi import Cookie, Depends

from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.user_field import get_user_create_internal_model, get_user_fields
from fief.dependencies.users import UserManager, get_user_manager
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.locale import gettext_lazy as _
from fief.models import RegistrationSession, Tenant, UserField
from fief.repositories import OAuthAccountRepository, RegistrationSessionRepository
from fief.schemas.user import UF, UserCreateInternal
from fief.services.registration_flow import RegistrationFlow
from fief.settings import settings


async def get_registration_flow(
    registration_session_repository: RegistrationSessionRepository = Depends(
        get_workspace_repository(RegistrationSessionRepository)
    ),
    oauth_account_repository: OAuthAccountRepository = Depends(
        get_workspace_repository(OAuthAccountRepository)
    ),
    user_manager: UserManager = Depends(get_user_manager),
    user_create_internal_model: Type[UserCreateInternal[UF]] = Depends(
        get_user_create_internal_model
    ),
    user_fields: List[UserField] = Depends(get_user_fields),
) -> RegistrationFlow:
    return RegistrationFlow(
        registration_session_repository,
        oauth_account_repository,
        user_manager,
        user_create_internal_model,
        user_fields,
    )


async def get_optional_registration_session(
    token: Optional[str] = Cookie(
        None, alias=settings.registration_session_cookie_name
    ),
    registration_session_repository: RegistrationSessionRepository = Depends(
        get_workspace_repository(RegistrationSessionRepository)
    ),
    tenant: Tenant = Depends(get_current_tenant),
) -> Optional[RegistrationSession]:
    if token is None:
        return None

    registration_session = await registration_session_repository.get_by_token(token)
    if registration_session is None:
        return None

    if registration_session.tenant_id != tenant.id:
        return None

    return registration_session
