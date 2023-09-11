from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin_api
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tenant import get_paginated_tenants, get_tenant_by_id_or_404
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client, OAuthProvider, Tenant
from fief.repositories import (
    ClientRepository,
    OAuthProviderRepository,
    TenantRepository,
    ThemeRepository,
)
from fief.schemas.generics import PaginatedResults
from fief.services.webhooks.models import (
    ClientCreated,
    TenantCreated,
    TenantDeleted,
    TenantUpdated,
)

router = APIRouter(dependencies=[Depends(is_authenticated_admin_api)])


@router.get(
    "/", name="tenants:list", response_model=PaginatedResults[schemas.tenant.Tenant]
)
async def list_tenants(
    paginated_tenants: PaginatedObjects[Tenant] = Depends(get_paginated_tenants),
) -> PaginatedResults[schemas.tenant.Tenant]:
    tenants, count = paginated_tenants
    return PaginatedResults(
        count=count,
        results=[schemas.tenant.Tenant.model_validate(tenant) for tenant in tenants],
    )


@router.get("/{id:uuid}", name="tenants:get", response_model=schemas.tenant.Tenant)
async def get_tenant(tenant: Tenant = Depends(get_tenant_by_id_or_404)) -> Tenant:
    return tenant


@router.post(
    "/",
    name="tenants:create",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.tenant.Tenant,
)
async def create_tenant(
    tenant_create: schemas.tenant.TenantCreate,
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    client_repository: ClientRepository = Depends(
        get_workspace_repository(ClientRepository)
    ),
    theme_repository: ThemeRepository = Depends(
        get_workspace_repository(ThemeRepository)
    ),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.tenant.Tenant:
    if tenant_create.theme_id is not None:
        theme = await theme_repository.get_by_id(tenant_create.theme_id)
        if theme is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.TENANT_CREATE_NOT_EXISTING_THEME,
            )

    oauth_providers: list[OAuthProvider] = []
    if tenant_create.oauth_providers is not None:
        for oauth_provider_id in tenant_create.oauth_providers:
            oauth_provider = await oauth_provider_repository.get_by_id(
                oauth_provider_id
            )
            if oauth_provider is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=APIErrorCode.TENANT_CREATE_NOT_EXISTING_OAUTH_PROVIDER,
                )
            oauth_providers.append(oauth_provider)

    slug = await repository.get_available_slug(tenant_create.name)
    tenant = Tenant(
        **tenant_create.model_dump(exclude={"oauth_providers"}),
        slug=slug,
        oauth_providers=oauth_providers,
    )

    tenant = await repository.create(tenant)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, tenant)
    trigger_webhooks(TenantCreated, tenant, schemas.tenant.Tenant)

    client = Client(
        name=f"{tenant.name}'s client",
        first_party=True,
        tenant=tenant,
        redirect_uris=["http://localhost:8000/docs/oauth2-redirect"],
    )
    await client_repository.create(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, client)
    trigger_webhooks(ClientCreated, client, schemas.client.Client)

    return schemas.tenant.Tenant.model_validate(tenant)


@router.patch("/{id:uuid}", name="tenants:update", response_model=schemas.tenant.Tenant)
async def update_tenant(
    tenant_update: schemas.tenant.TenantUpdate,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    theme_repository: ThemeRepository = Depends(
        get_workspace_repository(ThemeRepository)
    ),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.tenant.Tenant:
    if tenant_update.theme_id is not None:
        theme = await theme_repository.get_by_id(tenant_update.theme_id)
        if theme is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.TENANT_UPDATE_NOT_EXISTING_THEME,
            )

    if tenant_update.oauth_providers is not None:
        tenant.oauth_providers = []
        for oauth_provider_id in tenant_update.oauth_providers:
            oauth_provider = await oauth_provider_repository.get_by_id(
                oauth_provider_id
            )
            if oauth_provider is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=APIErrorCode.TENANT_UPDATE_NOT_EXISTING_OAUTH_PROVIDER,
                )
            tenant.oauth_providers.append(oauth_provider)

    tenant_update_dict = tenant_update.model_dump(
        exclude={"oauth_providers"}, exclude_unset=True
    )
    for field, value in tenant_update_dict.items():
        setattr(tenant, field, value)

    await repository.update(tenant)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, tenant)
    trigger_webhooks(TenantUpdated, tenant, schemas.tenant.Tenant)

    return schemas.tenant.Tenant.model_validate(tenant)


@router.delete(
    "/{id:uuid}",
    name="tenants:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_tenant(
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    await repository.delete(tenant)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, tenant)
    trigger_webhooks(TenantDeleted, tenant, schemas.tenant.Tenant)
