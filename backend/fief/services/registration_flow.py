from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import Request, Response

from fief.dependencies.users import UserManager
from fief.models import (
    OAuthAccount,
    RegistrationSession,
    RegistrationSessionFlow,
    Tenant,
    User,
    UserField,
)
from fief.repositories import OAuthAccountRepository, RegistrationSessionRepository
from fief.schemas.user import UF, UserCreateInternal
from fief.settings import settings

ResponseType = TypeVar("ResponseType", bound=Response)


class RegistrationFlow:
    def __init__(
        self,
        registration_session_repository: RegistrationSessionRepository,
        oauth_account_repository: OAuthAccountRepository,
        user_manager: UserManager,
        user_create_internal_model: Type[UserCreateInternal[UF]],
        user_fields: List[UserField],
    ) -> None:
        self.registration_session_repository = registration_session_repository
        self.oauth_account_repository = oauth_account_repository
        self.user_manager = user_manager
        self.user_create_internal_model = user_create_internal_model
        self.user_fields = user_fields

    async def create_registration_session(
        self,
        response: ResponseType,
        flow: RegistrationSessionFlow,
        *,
        tenant: Tenant,
        oauth_account: Optional[OAuthAccount] = None
    ) -> ResponseType:
        email = None
        oauth_account_id = None
        if oauth_account is not None:
            email = oauth_account.account_email
            oauth_account_id = oauth_account.id

        registration_session = RegistrationSession(
            flow=flow,
            email=email,
            oauth_account_id=oauth_account_id,
            tenant_id=tenant.id,
        )
        registration_session = await self.registration_session_repository.create(
            registration_session
        )

        response.set_cookie(
            settings.registration_session_cookie_name,
            registration_session.token,
            domain=settings.registration_session_cookie_domain,
            secure=settings.registration_session_cookie_secure,
        )

        return response

    async def delete_registration_session(
        self, response: ResponseType, registration_session: RegistrationSession
    ) -> ResponseType:
        response.delete_cookie(
            settings.registration_session_cookie_name,
            domain=settings.registration_session_cookie_domain,
        )
        await self.registration_session_repository.delete(registration_session)
        return response

    async def create_user(
        self,
        data: Dict[str, Any],
        tenant: Tenant,
        registration_session: RegistrationSession,
        request: Optional[Request] = None,
    ) -> User:
        user_create_dict: Dict[str, Any] = {**data, "tenant_id": tenant.id}
        if "password" not in user_create_dict:
            user_create_dict["password"] = self.user_manager.password_helper.generate()
        user_create = self.user_create_internal_model(**user_create_dict)
        user = await self.user_manager.create_with_fields(
            user_create,
            user_fields=self.user_fields,
            safe=True,
            request=request,
        )

        if registration_session.oauth_account is not None:
            registration_session.oauth_account.user = user
            await self.oauth_account_repository.update(
                registration_session.oauth_account
            )

        return user
