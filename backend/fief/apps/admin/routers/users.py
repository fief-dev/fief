from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi_users.manager import InvalidPasswordException, UserAlreadyExists
from sqlalchemy.orm import joinedload

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.users import (
    UserManager,
    get_paginated_users,
    get_user_manager_from_create_user_internal,
)
from fief.dependencies.workspace_managers import get_user_manager as get_user_db_manager
from fief.errors import APIErrorCode
from fief.managers import UserManager as UserDBManager
from fief.models import User
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
    user_create: schemas.user.UserCreateInternal,
    request: Request,
    user_manager: UserManager = Depends(get_user_manager_from_create_user_internal),
    user_db_manager: UserDBManager = Depends(get_user_db_manager),
):
    try:
        created_user = await user_manager.create(user_create, request=request)
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

    user = await user_db_manager.get_by_id(created_user.id, (joinedload(User.tenant),))

    return schemas.user.UserRead.from_orm(user)
