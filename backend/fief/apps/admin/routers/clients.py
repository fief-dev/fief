from fastapi import APIRouter, Depends

from fief import schemas
from fief.dependencies.client import get_paginated_clients
from fief.dependencies.pagination import PaginatedObjects
from fief.models import Client
from fief.schemas.generics import PaginatedResults

router = APIRouter()


@router.get("/")
async def list_clients(
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
) -> PaginatedResults[schemas.tenant.Tenant]:
    clients, count = paginated_clients
    return PaginatedResults(
        count=count,
        results=[schemas.client.Client.from_orm(client) for client in clients],
    )
