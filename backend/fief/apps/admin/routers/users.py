from fastapi import APIRouter, Depends

from fief import schemas
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.users import get_paginated_users
from fief.models import User
from fief.schemas.generics import PaginatedResults

router = APIRouter()


@router.get("/")
async def list_users(
    paginated_users: PaginatedObjects[User] = Depends(get_paginated_users),
) -> PaginatedResults[schemas.user.UserRead]:
    users, count = paginated_users
    return PaginatedResults(
        count=count,
        results=[schemas.user.UserRead.from_orm(user) for user in users],
    )
