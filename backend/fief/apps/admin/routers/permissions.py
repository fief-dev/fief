from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.permission import (
    get_paginated_permissions,
    get_permission_by_id_or_404,
)
from fief.dependencies.workspace_repositories import get_permission_repository
from fief.errors import APIErrorCode
from fief.models import Permission
from fief.repositories import PermissionRepository
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/",
    name="permissions:list",
    response_model=PaginatedResults[schemas.permission.Permission],
)
async def list_permissions(
    paginated_permissions: PaginatedObjects[Permission] = Depends(
        get_paginated_permissions
    ),
) -> PaginatedResults[schemas.permission.Permission]:
    permissions, count = paginated_permissions
    return PaginatedResults(
        count=count,
        results=[
            schemas.permission.Permission.from_orm(permission)
            for permission in permissions
        ],
    )


@router.post(
    "/",
    name="permissions:create",
    response_model=schemas.permission.Permission,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    permission_create: schemas.permission.PermissionCreate,
    repository: PermissionRepository = Depends(get_permission_repository),
) -> schemas.permission.Permission:
    existing_permission = await repository.get_by_codename(permission_create.codename)
    if existing_permission is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.PERMISSION_CREATE_CODENAME_ALREADY_EXISTS,
        )

    permission = Permission(**permission_create.dict())
    permission = await repository.create(permission)

    return schemas.permission.Permission.from_orm(permission)


@router.patch(
    "/{id:uuid}",
    name="permissions:update",
    response_model=schemas.permission.Permission,
)
async def update_permission(
    permission_update: schemas.permission.PermissionUpdate,
    permission: Permission = Depends(get_permission_by_id_or_404),
    repository: PermissionRepository = Depends(get_permission_repository),
) -> schemas.permission.Permission:
    updated_codename = permission_update.codename
    if updated_codename is not None and updated_codename != permission.codename:
        existing_permission = await repository.get_by_codename(updated_codename)
        if existing_permission is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.PERMISSION_UPDATE_CODENAME_ALREADY_EXISTS,
            )

    permission_update_dict = permission_update.dict(exclude_unset=True)
    for field, value in permission_update_dict.items():
        setattr(permission, field, value)

    await repository.update(permission)

    return schemas.permission.Permission.from_orm(permission)


@router.delete(
    "/{id:uuid}",
    name="permissions:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_permission(
    permission: Permission = Depends(get_permission_by_id_or_404),
    repository: PermissionRepository = Depends(get_permission_repository),
):
    await repository.delete(permission)
