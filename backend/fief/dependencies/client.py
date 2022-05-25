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
from fief.dependencies.workspace_repositories import get_client_repository
from fief.models import Client
from fief.repositories import ClientRepository


async def get_paginated_clients(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: ClientRepository = Depends(get_client_repository),
) -> Tuple[List[Client], int]:
    statement = select(Client)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_client_by_id_or_404(
    id: UUID4,
    repository: ClientRepository = Depends(get_client_repository),
) -> Client:
    client = await repository.get_by_id(id)

    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return client
