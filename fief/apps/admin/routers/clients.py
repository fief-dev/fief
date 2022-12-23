import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from fief import schemas
from fief.crypto.jwk import generate_jwk
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client
from fief.repositories import ClientRepository, TenantRepository
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
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> schemas.client.Client:
    tenant = await tenant_repository.get_by_id(client_create.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.CLIENT_CREATE_UNKNOWN_TENANT,
        )

    client = Client(**client_create.dict())
    client = await repository.create(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, client)

    return schemas.client.Client.from_orm(client)


@router.patch("/{id:uuid}", name="clients:update", response_model=schemas.client.Client)
async def update_client(
    client_update: schemas.client.ClientUpdate,
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> schemas.client.Client:
    client_update_dict = client_update.dict(exclude_unset=True)
    for field, value in client_update_dict.items():
        setattr(client, field, value)

    await repository.update(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)

    return schemas.client.Client.from_orm(client)


@router.post(
    "/{id:uuid}/encryption-key",
    name="clients:encryption_key",
    status_code=status.HTTP_201_CREATED,
)
async def create_encryption_key(
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    client.encrypt_jwk = key.export_public()
    await repository.update(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)

    return key.export(as_dict=True)
