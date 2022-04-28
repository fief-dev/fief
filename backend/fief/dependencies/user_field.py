from typing import List, Tuple

from fastapi import Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_managers import get_user_field_manager
from fief.managers import UserFieldManager
from fief.models import UserField


async def get_paginated_user_fields(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: UserFieldManager = Depends(get_user_field_manager),
) -> Tuple[List[UserField], int]:
    statement = select(UserField)
    return await get_paginated_objects(statement, pagination, ordering, manager)


async def get_user_field_by_id_or_404(
    id: UUID4,
    manager: UserFieldManager = Depends(get_user_field_manager),
) -> UserField:
    user_field = await manager.get_by_id(id)

    if user_field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user_field
