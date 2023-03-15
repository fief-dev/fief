import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.crypto.jwk import generate_jwk
from fief.dependencies.admin_authentication import is_authenticated_admin_api
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client
from fief.repositories import ClientRepository, TenantRepository
from fief.schemas.generics import PaginatedResults
from fief.services.webhooks.models import ClientCreated, ClientDeleted, ClientUpdated

router = APIRouter(dependencies=[Depends(is_authenticated_admin_api)])


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


@router.get("/{id:uuid}", name="clients:get", response_model=schemas.client.Client)
async def get_webhook(client: Client = Depends(get_client_by_id_or_404)) -> Client:
    return client


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
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
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
    trigger_webhooks(ClientCreated, client, schemas.client.Client)

    return schemas.client.Client.from_orm(client)


@router.patch("/{id:uuid}", name="clients:update", response_model=schemas.client.Client)
async def update_client(
    client_update: schemas.client.ClientUpdate,
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.client.Client:
    client_update_dict = client_update.dict(exclude_unset=True)
    for field, value in client_update_dict.items():
        setattr(client, field, value)

    await repository.update(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)
    trigger_webhooks(ClientUpdated, client, schemas.client.Client)

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
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    client.encrypt_jwk = key.export_public()
    await repository.update(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)
    trigger_webhooks(ClientUpdated, client, schemas.client.Client)

    return key.export(as_dict=True)


@router.delete(
    "/{id:uuid}",
    name="clients:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_client(
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    await repository.delete(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, client)
    trigger_webhooks(ClientDeleted, client, schemas.client.Client)
