import uuid
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import UUID4, ValidationError, create_model
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from fief.crypto.access_token import InvalidAccessToken, read_access_token
from fief.crypto.password import password_helper
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.repositories import get_repository
from fief.dependencies.request import get_request_json
from fief.dependencies.tasks import get_send_task
from fief.dependencies.tenant import (
    get_current_tenant,
)
from fief.dependencies.user_field import (
    get_admin_user_update_model,
    get_user_create_admin_model,
    get_user_fields,
    get_user_update_model,
)
from fief.dependencies.user_roles import get_user_roles_service
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import (
    OAuthAccount,
    Tenant,
    User,
    UserField,
    UserPermission,
    UserRole,
)
from fief.repositories import (
    EmailVerificationRepository,
    OAuthAccountRepository,
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.schemas.user import UF, UserCreateAdmin, UserUpdate, UserUpdateAdmin
from fief.services.acr import ACR
from fief.services.user_manager import UserManager
from fief.services.user_roles import UserRolesService
from fief.tasks import SendTask


async def get_user_manager(
    user_repository: UserRepository = Depends(UserRepository),
    email_verification_repository: EmailVerificationRepository = Depends(
        get_repository(EmailVerificationRepository)
    ),
    user_fields: list[UserField] = Depends(get_user_fields),
    send_task: SendTask = Depends(get_send_task),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
    user_roles: UserRolesService = Depends(get_user_roles_service),
):
    return UserManager(
        password_helper=password_helper,
        user_repository=user_repository,
        email_verification_repository=email_verification_repository,
        user_fields=user_fields,
        send_task=send_task,
        audit_logger=audit_logger,
        trigger_webhooks=trigger_webhooks,
        user_roles=user_roles,
    )


scheme = OAuth2AuthorizationCodeBearer(
    "/authorize",
    "/api/token",
    "/api/token",
    scopes={"openid": "openid"},
    auto_error=False,
)


def current_user(
    *, optional: bool = False, active: bool = True, acr: ACR = ACR.LEVEL_ZERO
):
    async def _current_user(
        token: str | None = Depends(scheme),
        tenant: Tenant = Depends(get_current_tenant),
        user_manager: UserManager = Depends(get_user_manager),
    ) -> User | None:
        if token is None:
            if optional:
                return None
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            claims = read_access_token(tenant.get_sign_jwk(), token)
            user_id = uuid.UUID(claims["sub"])
            acr_claim = ACR(claims["acr"])
            user = await user_manager.get(user_id, tenant.id)
        except (InvalidAccessToken, KeyError, ValueError) as e:
            if optional:
                return None
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e
        else:
            if active and not user.is_active:
                if optional:
                    return None
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

            valid_acr = acr_claim >= acr
            if not valid_acr:
                if optional:
                    return None
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=APIErrorCode.ACR_TOO_LOW,
                )
            return user

    return _current_user


current_active_user = current_user(active=True)
current_active_user_acr_level_1 = current_user(active=True, acr=ACR.LEVEL_ONE)


async def get_paginated_users(
    query: str | None = Query(None),
    email: str | None = Query(None),
    tenant: UUID4 | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: UserRepository = Depends(UserRepository),
    get_paginated_objects: GetPaginatedObjects[User] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[User]:
    statement = select(User).options(joinedload(User.tenant))
    if query is not None:
        statement = statement.where(User.email_lower.ilike(f"%{query}%"))
    if email is not None:
        statement = statement.where(User.email_lower == email.lower())
    if tenant is not None:
        statement = statement.where(User.tenant_id == tenant)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_user_by_id_or_404(
    id: UUID4,
    repository: UserRepository = Depends(UserRepository),
) -> User:
    user = await repository.get_by_id(id, (joinedload(User.tenant),))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user


async def get_paginated_user_permissions(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    user: User = Depends(get_user_by_id_or_404),
    user_permission_repository: UserPermissionRepository = Depends(
        get_repository(UserPermissionRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[UserPermission] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[UserPermission]:
    statement = user_permission_repository.get_by_user_statement(user.id)
    return await get_paginated_objects(
        statement, pagination, ordering, user_permission_repository
    )


async def get_user_permissions(
    user: User = Depends(get_user_by_id_or_404),
    user_permission_repository: UserPermissionRepository = Depends(
        get_repository(UserPermissionRepository)
    ),
) -> list[UserPermission]:
    statement = user_permission_repository.get_by_user_statement(user.id)
    return await user_permission_repository.list(statement)


async def get_paginated_user_roles(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    user: User = Depends(get_user_by_id_or_404),
    user_role_repository: UserRoleRepository = Depends(
        get_repository(UserRoleRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[UserRole] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[UserRole]:
    statement = user_role_repository.get_by_user_statement(user.id)
    return await get_paginated_objects(
        statement, pagination, ordering, user_role_repository
    )


async def get_user_roles(
    user: User = Depends(get_user_by_id_or_404),
    user_role_repository: UserRoleRepository = Depends(
        get_repository(UserRoleRepository)
    ),
) -> list[UserRole]:
    statement = user_role_repository.get_by_user_statement(user.id)
    return await user_role_repository.list(statement)


async def get_paginated_user_oauth_accounts(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    user: User = Depends(get_user_by_id_or_404),
    oauth_account_repository: OAuthAccountRepository = Depends(
        get_repository(OAuthAccountRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[OAuthAccount] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[OAuthAccount]:
    statement = oauth_account_repository.get_by_user_statement(user.id)
    return await get_paginated_objects(
        statement, pagination, ordering, oauth_account_repository
    )


async def get_user_oauth_accounts(
    user: User = Depends(get_user_by_id_or_404),
    oauth_account_repository: OAuthAccountRepository = Depends(
        get_repository(OAuthAccountRepository)
    ),
) -> list[OAuthAccount]:
    statement = oauth_account_repository.get_by_user_statement(user.id)
    return await oauth_account_repository.list(statement)


async def get_user_create_admin(
    json: dict[str, Any] = Depends(get_request_json),
    user_create_admin_model: type[UserCreateAdmin[UF]] = Depends(
        get_user_create_admin_model,
    ),
) -> UserCreateAdmin[UF]:
    body_model = create_model(
        "UserCreateAdminBody",
        body=(user_create_admin_model, ...),
    )
    try:
        validated_user_create = body_model(body=json)
    except ValidationError as e:
        raise RequestValidationError(e.errors()) from e
    else:
        return validated_user_create.body  # type: ignore


async def get_user_update(
    json: dict[str, Any] = Depends(get_request_json),
    user_update_model: type[UserUpdate[UF]] = Depends(get_user_update_model),
) -> UserUpdate[UF]:
    body_model = create_model(
        "UserUpdateBody",
        body=(user_update_model, ...),
    )
    try:
        validated_user_update = body_model(body=json)
    except ValidationError as e:
        raise RequestValidationError(e.errors()) from e
    else:
        return validated_user_update.body  # type: ignore


async def get_admin_user_update(
    json: dict[str, Any] = Depends(get_request_json),
    user_update_model: type[UserUpdateAdmin[UF]] = Depends(get_admin_user_update_model),
) -> UserUpdateAdmin[UF]:
    body_model = create_model(
        "UserUpdateAdminBody",
        body=(user_update_model, ...),
    )
    try:
        validated_user_update = body_model(body=json)
    except ValidationError as e:
        raise RequestValidationError(e.errors()) from e
    else:
        return validated_user_update.body  # type: ignore
