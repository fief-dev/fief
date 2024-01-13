from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.models import Client
from fief.repositories import ClientRepository


async def get_paginated_clients(
    query: str | None = Query(None),
    tenant: UUID4 | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: ClientRepository = Depends(ClientRepository),
    get_paginated_objects: GetPaginatedObjects[Client] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[Client]:
    statement = select(Client)

    if query is not None:
        statement = statement.where(Client.name.ilike(f"%{query}%"))

    if tenant is not None:
        statement = statement.where(Client.tenant_id == tenant)

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_client_by_id_or_404(
    id: UUID4,
    repository: ClientRepository = Depends(ClientRepository),
) -> Client:
    client = await repository.get_by_id(id)

    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return client
