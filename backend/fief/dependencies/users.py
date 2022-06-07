from typing import Dict, List, Optional, Type, Union, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_users import BaseUserManager, InvalidPasswordException
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    Strategy,
)
from fastapi_users.exceptions import UserNotExists
from fastapi_users.manager import UUIDIDMixin
from fastapi_users.password import PasswordHelperProtocol
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseOAuthAccountTable,
    SQLAlchemyUserDatabase,
)
from furl import furl
from jwcrypto import jwk
from pydantic import UUID4, ValidationError, create_model
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
from fief.dependencies.user_field import (
    get_admin_user_create_internal_model,
    get_admin_user_update_model,
    get_user_update_model,
)
from fief.dependencies.workspace_repositories import (
    get_user_permission_repository,
    get_user_repository,
    get_user_role_repository,
)
from fief.locale import Translations
from fief.models import (
    Tenant,
    User,
    UserField,
    UserFieldValue,
    UserPermission,
    UserRole,
    Workspace,
)
from fief.repositories import (
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.schemas.user import UF, UserCreate, UserCreateInternal, UserUpdate
from fief.settings import settings
from fief.tasks import SendTask, on_after_forgot_password, on_after_register


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID4]):
    reset_password_token_secret = settings.secret.get_secret_value()
    verification_token_secret = settings.secret.get_secret_value()

    def __init__(
        self,
        user_db: SQLAlchemyUserDatabase[User, UUID4],
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

    async def validate_password(  # type: ignore
        self, password: str, user: Union[UserCreate, User]
    ) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(
                reason=self.translations.gettext(
                    "The password should be at least 8 characters."
                )
            )

    async def create_with_fields(
        self,
        user_create: UserCreate[UF],
        *,
        user_fields: List[UserField],
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        user = await self.create(user_create, safe, request)

        for user_field in user_fields:
            user_field_value = UserFieldValue(user_field=user_field)
            try:
                value = user_create.fields.get_value(user_field.slug)
                if value is not None:
                    user_field_value.value = value
                    user.user_field_values.append(user_field_value)
            except AttributeError:
                default = user_field.get_default()
                if default is not None:
                    user_field_value.value = default
                    user.user_field_values.append(user_field_value)

        return await self.user_db.update(user, {})

    async def update_with_fields(
        self,
        user_update: UserUpdate[UF],
        user: User,
        *,
        user_fields: List[UserField],
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        user = await self.update(user_update, user, safe, request)

        if user_update.fields is not None:
            for user_field in user_fields:
                existing_user_field_value = user.get_user_field_value(user_field)
                # Update existing value
                if existing_user_field_value is not None:
                    try:
                        value = user_update.fields.get_value(user_field.slug)
                        if value is not None:
                            existing_user_field_value.value = value
                    except AttributeError:
                        pass
                # Create new value
                else:
                    user_field_value = UserFieldValue(user_field=user_field)
                    try:
                        value = user_update.fields.get_value(user_field.slug)
                        if value is not None:
                            user_field_value.value = value
                            user.user_field_values.append(user_field_value)
                    except AttributeError:
                        default = user_field.get_default()
                        if default is not None:
                            user_field_value.value = default
                            user.user_field_values.append(user_field_value)

            user = await self.user_db.update(user, {})

        return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        self.send_task(on_after_register, str(user.id), str(self.workspace.id))

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
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
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


class SQLAlchemyUserTenantDatabase(SQLAlchemyUserDatabase[User, UUID4]):
    def __init__(
        self,
        session: AsyncSession,
        tenant: Tenant,
        user_table: Type[User],
        oauth_account_table: Optional[Type[SQLAlchemyBaseOAuthAccountTable]] = None,
    ):
        super().__init__(session, user_table, oauth_account_table=oauth_account_table)
        self.tenant = tenant

    async def _get_user(self, statement: Select) -> Optional[User]:
        statement = statement.where(User.tenant_id == self.tenant.id)
        return await super()._get_user(statement)


class JWTAccessTokenStrategy(Strategy[User, UUID4]):
    def __init__(self, key: jwk.JWK):
        self.key = key

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[User, UUID4]
    ) -> Optional[User]:
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
) -> SQLAlchemyUserDatabase[User, UUID4]:
    return SQLAlchemyUserTenantDatabase(session, tenant, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, UUID4] = Depends(get_user_db),
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
) -> SQLAlchemyUserDatabase[User, UUID4]:
    return SQLAlchemyUserTenantDatabase(session, tenant, User)


async def get_user_manager_from_create_user_internal(
    user_db: SQLAlchemyUserDatabase[User, UUID4] = Depends(
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


authentication_backend = AuthenticationBackend[User, UUID4](
    "jwt_access_token",
    AuthorizationCodeBearerTransport(
        "/authorize", "/api/token", "/api/token", {"openid": "openid"}
    ),
    get_jwt_access_token_strategy,
)


async def get_paginated_users(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: UserRepository = Depends(get_user_repository),
) -> PaginatedObjects[User]:
    statement = select(User).options(joinedload(User.tenant))
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_user_by_id_or_404(
    id: UUID4,
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    user = await repository.get_by_id(id, (joinedload(User.tenant),))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user


async def get_paginated_user_permissions(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    user: User = Depends(get_user_by_id_or_404),
    user_permission_repository: UserPermissionRepository = Depends(
        get_user_permission_repository
    ),
) -> PaginatedObjects[UserPermission]:
    statement = user_permission_repository.get_by_user_statement(user.id)
    return await get_paginated_objects(
        statement, pagination, ordering, user_permission_repository
    )


async def get_paginated_user_roles(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    user: User = Depends(get_user_by_id_or_404),
    user_role_repository: UserRoleRepository = Depends(get_user_role_repository),
) -> PaginatedObjects[UserRole]:
    statement = user_role_repository.get_by_user_statement(user.id)
    return await get_paginated_objects(
        statement, pagination, ordering, user_role_repository
    )


async def get_user_db_from_user(
    user: User = Depends(get_user_by_id_or_404),
    session: AsyncSession = Depends(get_current_workspace_session),
) -> SQLAlchemyUserDatabase[User, UUID4]:
    return SQLAlchemyUserTenantDatabase(session, user.tenant, User)


async def get_user_manager_from_user(
    user: User = Depends(get_user_by_id_or_404),
    user_db: SQLAlchemyUserDatabase[User, UUID4] = Depends(get_user_db_from_user),
    workspace: Workspace = Depends(get_current_workspace),
    translations: Translations = Depends(get_translations),
    send_task: SendTask = Depends(get_send_task),
):
    return UserManager(
        user_db, password_helper, workspace, user.tenant, translations, send_task
    )


async def get_user_create_internal(
    request: Request,
    user_create_internal_model: Type[UserCreateInternal[UF]] = Depends(
        get_admin_user_create_internal_model
    ),
) -> UserCreateInternal[UF]:
    body_model = create_model(
        "UserCreateInternalBody",
        body=(user_create_internal_model, ...),
    )
    try:
        validated_user_create_internal = body_model(body=await request.json())
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e
    else:
        return validated_user_create_internal.body  # type: ignore


async def get_user_update(
    request: Request,
    user_update_model: Type[UserUpdate[UF]] = Depends(get_user_update_model),
) -> UserUpdate[UF]:
    body_model = create_model(
        "UserUpdateBody",
        body=(user_update_model, ...),
    )
    try:
        validated_user_update = body_model(body=await request.json())
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e
    else:
        return validated_user_update.body  # type: ignore


async def get_admin_user_update(
    request: Request,
    user_update_model: Type[UserUpdate[UF]] = Depends(get_admin_user_update_model),
) -> UserUpdate[UF]:
    body_model = create_model(
        "UserUpdateBody",
        body=(user_update_model, ...),
    )
    try:
        validated_user_update = body_model(body=await request.json())
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e
    else:
        return validated_user_update.body  # type: ignore
