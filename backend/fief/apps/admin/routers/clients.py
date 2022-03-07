import secrets

from fastapi import APIRouter, Depends, status

from fief import schemas
from fief.crypto.jwk import generate_jwk
from fief.dependencies.account_managers import get_client_manager
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.pagination import PaginatedObjects
from fief.managers import ClientManager
from fief.models import Client
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


@router.get("/", name="clients:list")
async def list_clients(
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
) -> PaginatedResults[schemas.tenant.Tenant]:
    clients, count = paginated_clients
    return PaginatedResults(
        count=count,
        results=[schemas.client.Client.from_orm(client) for client in clients],
    )


@router.post(
    "/{id:uuid}/encryption-key",
    name="clients:encryption_key",
    status_code=status.HTTP_201_CREATED,
)
async def create_encryption_key(
    client: Client = Depends(get_client_by_id_or_404),
    manager: ClientManager = Depends(get_client_manager),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    client.encrypt_jwk = key.export_public()
    await manager.update(client)

    return key.export(as_dict=True)
