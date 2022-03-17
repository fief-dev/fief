import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from fief import schemas
from fief.crypto.jwk import generate_jwk
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace_managers import get_client_manager, get_tenant_manager
from fief.errors import APIErrorCode
from fief.managers import ClientManager, TenantManager
from fief.models import Client
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/", name="clients:list", response_model=PaginatedResults[schemas.client.Client]
)
async def list_clients(
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
) -> PaginatedResults[schemas.client.Client]:
    clients, count = paginated_clients
    return PaginatedResults(
        count=count,
        results=[schemas.client.Client.from_orm(client) for client in clients],
    )


@router.post(
    "/",
    name="clients:create",
    response_model=schemas.client.Client,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    client_create: schemas.client.ClientCreate,
    manager: ClientManager = Depends(get_client_manager),
    tenant_manager: TenantManager = Depends(get_tenant_manager),
) -> schemas.client.Client:
    tenant = await tenant_manager.get_by_id(client_create.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.CLIENT_CREATE_UNKNOWN_TENANT,
        )

    client = Client(**client_create.dict())
    client = await manager.create(client)

    return schemas.client.Client.from_orm(client)


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
