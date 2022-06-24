from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from pydantic import UUID4
from sqlalchemy.orm import joinedload

from fief import schemas, tasks
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tasks import get_send_task
from fief.dependencies.user_field import get_user_fields
from fief.dependencies.users import (
    UserManager,
    get_admin_user_update,
    get_paginated_user_permissions,
    get_paginated_user_roles,
    get_paginated_users,
    get_user_by_id_or_404,
    get_user_create_internal,
    get_user_manager_from_create_user_internal,
    get_user_manager_from_user,
)
from fief.dependencies.workspace_repositories import (
    get_permission_repository,
    get_role_repository,
    get_user_permission_repository,
    get_user_repository,
    get_user_role_repository,
)
from fief.errors import APIErrorCode
from fief.models import User, UserField, UserPermission, UserRole, Workspace
from fief.repositories import (
    PermissionRepository,
    RoleRepository,
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.schemas.generics import PaginatedResults
from fief.tasks import SendTask

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/", name="users:list", response_model=PaginatedResults[schemas.user.UserRead]
)
async def list_users(
    paginated_users: PaginatedObjects[User] = Depends(get_paginated_users),
) -> PaginatedResults[schemas.user.UserRead]:
    users, count = paginated_users
    return PaginatedResults(
        count=count,
        results=[schemas.user.UserRead.from_orm(user) for user in users],
    )


@router.get("/{id:uuid}", name="users:get", response_model=schemas.user.UserRead)
async def get_user(
    user: User = Depends(get_user_by_id_or_404),
) -> schemas.user.UserRead:
    return schemas.user.UserRead.from_orm(user)


@router.post(
    "/",
    name="users:create",
    response_model=schemas.user.UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: Request,
    user_create: schemas.user.UserCreateInternal = Depends(get_user_create_internal),
    user_fields: List[UserField] = Depends(get_user_fields),
    user_manager: UserManager = Depends(get_user_manager_from_create_user_internal),
    user_repository: UserRepository = Depends(get_user_repository),
):
    try:
        created_user = await user_manager.create_with_fields(
            user_create, user_fields=user_fields, request=request
        )
    except UserAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_CREATE_ALREADY_EXISTS,
        ) from e
    except InvalidPasswordException as e:
        # Build a JSON response manually to fine-tune the response structure
        return JSONResponse(
            content={
                "detail": APIErrorCode.USER_CREATE_INVALID_PASSWORD,
                "reason": str(e.reason),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = await user_repository.get_by_id(created_user.id, (joinedload(User.tenant),))

    return schemas.user.UserRead.from_orm(user)


@router.patch("/{id:uuid}", name="users:update", response_model=schemas.user.UserRead)
async def update_user(
    request: Request,
    user_update: schemas.user.UserUpdate = Depends(get_admin_user_update),
    user: User = Depends(get_user_by_id_or_404),
    user_fields: List[UserField] = Depends(get_user_fields),
    user_manager: UserManager = Depends(get_user_manager_from_user),
):
    try:
        user = await user_manager.update_with_fields(
            user_update,
            user,
            user_fields=user_fields,
            safe=False,
            request=request,
        )
    except UserAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS,
        ) from e
    except InvalidPasswordException as e:
        # Build a JSON response manually to fine-tune the response structure
        return JSONResponse(
            content={
                "detail": APIErrorCode.USER_UPDATE_INVALID_PASSWORD,
                "reason": str(e.reason),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return schemas.user.UserRead.from_orm(user)


@router.get(
    "/{id:uuid}/permissions",
    name="users:list_permissions",
    response_model=PaginatedResults[schemas.user_permission.UserPermission],
)
async def list_user_permissions(
    paginated_user_permissions: PaginatedObjects[UserPermission] = Depends(
        get_paginated_user_permissions
    ),
) -> PaginatedResults[schemas.user_permission.UserPermission]:
    user_permissions, count = paginated_user_permissions
    return PaginatedResults(
        count=count,
        results=[
            schemas.user_permission.UserPermission.from_orm(user_permission)
            for user_permission in user_permissions
        ],
    )


@router.post(
    "/{id:uuid}/permissions",
    name="users:create_permission",
    status_code=status.HTTP_201_CREATED,
)
async def create_user_permission(
    user_permission_create: schemas.user_permission.UserPermissionCreate,
    user: User = Depends(get_user_by_id_or_404),
    permission_repository: PermissionRepository = Depends(get_permission_repository),
    user_permission_repository: UserPermissionRepository = Depends(
        get_user_permission_repository
    ),
) -> None:
    permission_id = user_permission_create.id
    permission = await permission_repository.get_by_id(permission_id)

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_PERMISSION_CREATE_NOT_EXISTING_PERMISSION,
        )

    existing_user_permission = (
        await user_permission_repository.get_by_permission_and_user(
            user.id, permission_id, direct_only=True
        )
    )
    if existing_user_permission is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_PERMISSION_CREATE_ALREADY_ADDED_PERMISSION,
        )

    user_permission = UserPermission(user_id=user.id, permission_id=permission_id)
    await user_permission_repository.create(user_permission)


@router.delete(
    "/{id:uuid}/permissions/{permission_id:uuid}",
    name="users:delete_permission",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user_permission(
    permission_id: UUID4,
    user: User = Depends(get_user_by_id_or_404),
    user_permission_repository: UserPermissionRepository = Depends(
        get_user_permission_repository
    ),
) -> None:
    user_permission = await user_permission_repository.get_by_permission_and_user(
        user.id, permission_id, direct_only=True
    )
    if user_permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await user_permission_repository.delete(user_permission)


@router.get(
    "/{id:uuid}/roles",
    name="users:list_roles",
    response_model=PaginatedResults[schemas.user_role.UserRole],
)
async def list_user_roles(
    paginated_user_roles: PaginatedObjects[UserRole] = Depends(
        get_paginated_user_roles
    ),
) -> PaginatedResults[schemas.user_role.UserRole]:
    user_roles, count = paginated_user_roles
    return PaginatedResults(
        count=count,
        results=[
            schemas.user_role.UserRole.from_orm(user_role) for user_role in user_roles
        ],
    )


@router.post(
    "/{id:uuid}/roles", name="users:create_role", status_code=status.HTTP_201_CREATED
)
async def create_user_role(
    user_role_create: schemas.user_role.UserRoleCreate,
    user: User = Depends(get_user_by_id_or_404),
    role_repository: RoleRepository = Depends(get_role_repository),
    user_role_repository: UserRoleRepository = Depends(get_user_role_repository),
    workspace: Workspace = Depends(get_current_workspace),
    send_task: SendTask = Depends(get_send_task),
) -> None:
    role_id = user_role_create.id
    role = await role_repository.get_by_id(role_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_ROLE_CREATE_NOT_EXISTING_ROLE,
        )

    existing_user_role = await user_role_repository.get_by_role_and_user(
        user.id, role_id
    )
    if existing_user_role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_ROLE_CREATE_ALREADY_ADDED_ROLE,
        )

    user_role = UserRole(user_id=user.id, role_id=role_id)
    await user_role_repository.create(user_role)

    send_task(tasks.on_user_role_created, str(user.id), str(role.id), str(workspace.id))


@router.delete(
    "/{id:uuid}/roles/{role_id:uuid}",
    name="users:delete_role",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user_role(
    role_id: UUID4,
    user: User = Depends(get_user_by_id_or_404),
    user_role_repository: UserRoleRepository = Depends(get_user_role_repository),
    workspace: Workspace = Depends(get_current_workspace),
    send_task: SendTask = Depends(get_send_task),
) -> None:
    user_role = await user_role_repository.get_by_role_and_user(user.id, role_id)
    if user_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await user_role_repository.delete(user_role)

    send_task(tasks.on_user_role_deleted, str(user.id), str(role_id), str(workspace.id))
