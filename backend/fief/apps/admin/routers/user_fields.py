from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.user_field import (
    get_paginated_user_fields,
    get_user_field_by_id_or_404,
    get_validated_user_field_create,
    get_validated_user_field_update,
)
from fief.dependencies.workspace_repositories import get_user_field_repository
from fief.errors import APIErrorCode
from fief.models import UserField
from fief.repositories import UserFieldRepository
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/",
    name="user_fields:list",
    response_model=PaginatedResults[schemas.user_field.UserField],
)
async def list_user_fields(
    paginated_user_fields: PaginatedObjects[UserField] = Depends(
        get_paginated_user_fields
    ),
) -> PaginatedResults[schemas.user_field.UserField]:
    user_fields, count = paginated_user_fields
    return PaginatedResults(
        count=count,
        results=[
            schemas.user_field.UserField.from_orm(user_field)
            for user_field in user_fields
        ],
    )


@router.post(
    "/",
    name="user_fields:create",
    response_model=schemas.user_field.UserField,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_field(
    user_field_create: schemas.user_field.UserFieldCreate = Depends(
        get_validated_user_field_create
    ),
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> schemas.user_field.UserField:
    existing_user_field = await repository.get_by_slug(user_field_create.slug)
    if existing_user_field is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS,
        )

    user_field = UserField(**user_field_create.dict())
    user_field = await repository.create(user_field)

    return schemas.user_field.UserField.from_orm(user_field)


@router.patch(
    "/{id:uuid}", name="user_fields:update", response_model=schemas.user_field.UserField
)
async def update_user_field(
    user_field_update: schemas.user_field.UserFieldUpdate = Depends(
        get_validated_user_field_update
    ),
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> schemas.user_field.UserField:
    updated_slug = user_field_update.slug
    if updated_slug is not None and updated_slug != user_field.slug:
        existing_user_field = await repository.get_by_slug(updated_slug)
        if existing_user_field is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS,
            )

    user_field_update_dict = user_field_update.dict(exclude_unset=True)
    for field, value in user_field_update_dict.items():
        setattr(user_field, field, value)

    await repository.update(user_field)

    return schemas.user_field.UserField.from_orm(user_field)


@router.delete(
    "/{id:uuid}",
    name="user_fields:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user_field(
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(get_user_field_repository),
):
    await repository.delete(user_field)
