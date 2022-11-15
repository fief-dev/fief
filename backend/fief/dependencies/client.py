from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import Client
from fief.repositories import ClientRepository


async def get_paginated_clients(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
) -> tuple[list[Client], int]:
    statement = select(Client)

    if query is not None:
        statement = statement.where(Client.name.ilike(f"%{query}%"))

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_client_by_id_or_404(
    id: UUID4,
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
) -> Client:
    client = await repository.get_by_id(id)

    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return client
