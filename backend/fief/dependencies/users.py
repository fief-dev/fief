from typing import Dict, Optional, Type, Union, cast

from fastapi import Depends, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_users import BaseUserManager, InvalidPasswordException
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    Strategy,
)
from fastapi_users.manager import UserNotExists
from fastapi_users.password import PasswordHelperProtocol
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseOAuthAccountTable,
    SQLAlchemyBaseUserTable,
    SQLAlchemyUserDatabase,
)
from furl import furl
from jwcrypto import jwk
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select

from fief.crypto.access_token import InvalidAccessToken, read_access_token
from fief.crypto.password import password_helper
from fief.db import AsyncSession
from fief.dependencies.current_workspace import (
    get_current_workspace,
    get_current_workspace_session,
)
from fief.dependencies.locale import get_translations
from fief.dependencies.pagination import (
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.tasks import get_send_task
from fief.dependencies.tenant import (
    get_current_tenant,
    get_tenant_from_create_user_internal,
)
from fief.dependencies.workspace_managers import get_user_manager as get_user_db_manager
from fief.locale import Translations
from fief.managers import UserManager as UserDBManager
from fief.models import Tenant, User, Workspace
from fief.schemas.user import UserCreate, UserDB
from fief.settings import settings
from fief.tasks import SendTask, on_after_forgot_password, on_after_register


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = settings.secret.get_secret_value()
    verification_token_secret = settings.secret.get_secret_value()

    def __init__(
        self,
        user_db: SQLAlchemyUserDatabase[UserDB],
        password_helper: PasswordHelperProtocol,
        workspace: Workspace,
        tenant: Tenant,
        translations: Translations,
        send_task: SendTask,
    ):
        super().__init__(user_db, password_helper)
        self.workspace = workspace
        self.tenant = tenant
        self.translations = translations
        self.send_task = send_task

    async def validate_password(
        self, password: str, user: Union[UserCreate, UserDB]
    ) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(
                reason=self.translations.gettext(
                    "The password should be at least 8 characters."
                )
            )

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        self.send_task(on_after_register, str(user.id), str(self.workspace.id))

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        reset_url = furl(self.tenant.url_for(cast(Request, request), "reset:reset.get"))
        reset_url.add(query_params={"token": token})
        self.send_task(
            on_after_forgot_password,
            str(user.id),
            str(self.workspace.id),
            reset_url.url,
        )

    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


class SQLAlchemyUserTenantDatabase(SQLAlchemyUserDatabase[UserDB]):
    def __init__(
        self,
        user_db_model: Type[UserDB],
        session: AsyncSession,
        tenant: Tenant,
        user_table: Type[User],
        oauth_account_table: Optional[Type[SQLAlchemyBaseOAuthAccountTable]] = None,
    ):
        super().__init__(
            user_db_model,
            session,
            cast(Type[SQLAlchemyBaseUserTable], user_table),
            oauth_account_table=oauth_account_table,
        )
        self.tenant = tenant

    async def _get_user(self, statement: Select) -> Optional[UserDB]:
        statement = statement.where(User.tenant_id == self.tenant.id)
        return await super()._get_user(statement)


class JWTAccessTokenStrategy(Strategy[UserCreate, UserDB]):
    def __init__(self, key: jwk.JWK):
        self.key = key

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[UserCreate, UserDB]
    ) -> Optional[UserDB]:
        if token is None:
            return None

        try:
            user_id = read_access_token(self.key, token)
            user = await user_manager.get(user_id)
        except InvalidAccessToken:
            return None
        except UserNotExists:
            return None
        else:
            return user


async def get_jwt_access_token_strategy(
    tenant: Tenant = Depends(get_current_tenant),
) -> JWTAccessTokenStrategy:
    return JWTAccessTokenStrategy(tenant.get_sign_jwk())


async def get_user_db(
    session: AsyncSession = Depends(get_current_workspace_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> SQLAlchemyUserDatabase[UserDB]:
    return SQLAlchemyUserTenantDatabase(UserDB, session, tenant, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[UserDB] = Depends(get_user_db),
    tenant: Tenant = Depends(get_current_tenant),
    workspace: Workspace = Depends(get_current_workspace),
    translations: Translations = Depends(get_translations),
    send_task: SendTask = Depends(get_send_task),
):
    return UserManager(
        user_db, password_helper, workspace, tenant, translations, send_task
    )


async def get_user_db_from_create_user_internal(
    session: AsyncSession = Depends(get_current_workspace_session),
    tenant: Tenant = Depends(get_tenant_from_create_user_internal),
) -> SQLAlchemyUserDatabase[UserDB]:
    return SQLAlchemyUserTenantDatabase(UserDB, session, tenant, User)


async def get_user_manager_from_create_user_internal(
    user_db: SQLAlchemyUserDatabase[UserDB] = Depends(
        get_user_db_from_create_user_internal
    ),
    tenant: Tenant = Depends(get_tenant_from_create_user_internal),
    workspace: Workspace = Depends(get_current_workspace),
    translations: Translations = Depends(get_translations),
    send_task: SendTask = Depends(get_send_task),
):
    return UserManager(
        user_db, password_helper, workspace, tenant, translations, send_task
    )


class AuthorizationCodeBearerTransport(BearerTransport):
    scheme: OAuth2AuthorizationCodeBearer  # type: ignore

    def __init__(
        self,
        authorizationUrl: str,
        tokenUrl: str,
        refreshUrl: str,
        scopes: Dict[str, str],
    ):
        self.scheme = OAuth2AuthorizationCodeBearer(
            authorizationUrl, tokenUrl, refreshUrl, scopes=scopes
        )


authentication_backend = AuthenticationBackend[UserCreate, UserDB](
    "jwt_access_token",
    AuthorizationCodeBearerTransport(
        "/authorize", "/api/token", "/api/token", {"openid": "openid"}
    ),
    get_jwt_access_token_strategy,
)


async def get_paginated_users(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: UserDBManager = Depends(get_user_db_manager),
) -> PaginatedObjects[User]:
    statement = select(User).options(joinedload(User.tenant))
    return await get_paginated_objects(statement, pagination, ordering, manager)
