from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import joinedload

from fief import schemas
from fief.dependencies.account_managers import get_user_manager as get_user_db_manager
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.users import (
    UserManager,
    get_paginated_users,
    get_user_manager_from_create_user_internal,
)
from fief.managers import UserManager as UserDBManager
from fief.models import User
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


@router.get("/", name="users:list")
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
) -> schemas.user.UserRead:
    created_user = await user_manager.create(user_create, request=request)

    user = await user_db_manager.get_by_id(created_user.id, (joinedload(User.tenant),))

    return schemas.user.UserRead.from_orm(user)
