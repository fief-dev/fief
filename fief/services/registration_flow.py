import urllib.parse
from typing import Any, TypeVar

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
        user_create_internal_model: type[UserCreateInternal[UF]],
        user_fields: list[UserField],
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
        oauth_account: OAuthAccount | None = None,
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

    async def set_login_hint(
        self, response: ResponseType, registration_session: RegistrationSession
    ) -> ResponseType:
        login_hint = registration_session.email

        if registration_session.oauth_account:
            login_hint = str(registration_session.oauth_account.oauth_provider_id)

        if login_hint is None:
            return response

        response.set_cookie(
            settings.login_hint_cookie_name,
            value=urllib.parse.quote(login_hint),
            max_age=settings.login_hint_cookie_lifetime_seconds,
            domain=settings.login_hint_cookie_domain,
            secure=settings.login_hint_cookie_secure,
            httponly=True,
        )

        return response

    async def create_user(
        self,
        data: dict[str, Any],
        tenant: Tenant,
        registration_session: RegistrationSession,
        request: Request | None = None,
    ) -> User:
        user_create_dict: dict[str, Any] = {**data, "tenant_id": tenant.id}
        if "password" not in user_create_dict:
            user_create_dict["password"] = self.user_manager.password_helper.generate()
        user_create = self.user_create_internal_model(**user_create_dict)
        user = await self.user_manager.create_with_fields(
            user_create,
            user_fields=self.user_fields,
            safe=True,
            request=request,
        )

        registration_session.email = user.email
        await self.registration_session_repository.update(registration_session)

        if registration_session.oauth_account is not None:
            registration_session.oauth_account.user = user
            await self.oauth_account_repository.update(
                registration_session.oauth_account
            )

        return user
