from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from sqlalchemy.orm import joinedload

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.user_field import get_user_fields
from fief.dependencies.users import (
    UserManager,
    get_admin_user_update,
    get_paginated_users,
    get_user_by_id_or_404,
    get_user_create_internal,
    get_user_manager_from_create_user_internal,
    get_user_manager_from_user,
)
from fief.dependencies.workspace_repositories import get_user_repository
from fief.errors import APIErrorCode
from fief.models import User, UserField
from fief.repositories import UserRepository
from fief.schemas.generics import PaginatedResults

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
                "reason": e.reason,
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
                "reason": e.reason,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return schemas.user.UserRead.from_orm(user)
