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
from fief.dependencies.workspace_managers import get_client_manager
from fief.managers import ClientManager
from fief.models import Client


async def get_paginated_clients(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: ClientManager = Depends(get_client_manager),
) -> Tuple[List[Client], int]:
    statement = select(Client)
    return await get_paginated_objects(statement, pagination, ordering, manager)


async def get_client_by_id_or_404(
    id: UUID4,
    manager: ClientManager = Depends(get_client_manager),
) -> Client:
    client = await manager.get_by_id(id)

    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return client
