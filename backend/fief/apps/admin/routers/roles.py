from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.role import get_paginated_roles, get_role_by_id_or_404
from fief.dependencies.tasks import get_send_task
from fief.dependencies.workspace_repositories import (
    get_permission_repository,
    get_role_repository,
)
from fief.errors import APIErrorCode
from fief.models import Role, Workspace
from fief.repositories import PermissionRepository, RoleRepository
from fief.schemas.generics import PaginatedResults
from fief.tasks import SendTask, on_role_updated

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/",
    name="roles:list",
    response_model=PaginatedResults[schemas.role.Role],
)
async def list_roles(
    paginated_roles: PaginatedObjects[Role] = Depends(get_paginated_roles),
) -> PaginatedResults[schemas.role.Role]:
    roles, count = paginated_roles
    return PaginatedResults(
        count=count,
        results=[schemas.role.Role.from_orm(role) for role in roles],
    )


@router.post(
    "/",
    name="roles:create",
    response_model=schemas.role.Role,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    role_create: schemas.role.RoleCreate,
    repository: RoleRepository = Depends(get_role_repository),
    permission_repository: PermissionRepository = Depends(get_permission_repository),
) -> schemas.role.Role:
    role = Role(**role_create.dict(exclude={"permissions"}))

    for permission_id in role_create.permissions:
        permission = await permission_repository.get_by_id(permission_id)
        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.ROLE_CREATE_NOT_EXISTING_PERMISSION,
            )
        else:
            role.permissions.append(permission)

    role = await repository.create(role)

    return schemas.role.Role.from_orm(role)


@router.patch(
    "/{id:uuid}",
    name="roles:update",
    response_model=schemas.role.Role,
)
async def update_role(
    role_update: schemas.role.RoleUpdate,
    role: Role = Depends(get_role_by_id_or_404),
    repository: RoleRepository = Depends(get_role_repository),
    permission_repository: PermissionRepository = Depends(get_permission_repository),
    send_task: SendTask = Depends(get_send_task),
    workspace: Workspace = Depends(get_current_workspace),
) -> schemas.role.Role:
    role_update_dict = role_update.dict(exclude_unset=True, exclude={"permissions"})
    for field, value in role_update_dict.items():
        setattr(role, field, value)

    old_permissions = {permission.id for permission in role.permissions}
    if role_update.permissions is not None:
        role.permissions = []
        for permission_id in role_update.permissions:
            permission = await permission_repository.get_by_id(permission_id)
            if permission is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIErrorCode.ROLE_UPDATE_NOT_EXISTING_PERMISSION,
                )
            else:
                role.permissions.append(permission)
    new_permissions = {permission.id for permission in role.permissions}

    await repository.update(role)

    added_permissions = new_permissions - old_permissions
    deleted_permissions = old_permissions - new_permissions
    send_task(
        on_role_updated,
        str(role.id),
        list(map(str, added_permissions)),
        list(map(str, deleted_permissions)),
        str(workspace.id),
    )

    return schemas.role.Role.from_orm(role)


@router.delete(
    "/{id:uuid}",
    name="roles:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_role(
    role: Role = Depends(get_role_by_id_or_404),
    repository: RoleRepository = Depends(get_role_repository),
):
    await repository.delete(role)
