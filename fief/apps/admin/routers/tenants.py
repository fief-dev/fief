from fastapi import APIRouter, Depends, HTTPException, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tenant import get_paginated_tenants, get_tenant_by_id_or_404
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client, Tenant
from fief.repositories import ClientRepository, TenantRepository, ThemeRepository
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/", name="tenants:list", response_model=PaginatedResults[schemas.tenant.Tenant]
)
async def list_tenants(
    paginated_tenants: PaginatedObjects[Tenant] = Depends(get_paginated_tenants),
) -> PaginatedResults[schemas.tenant.Tenant]:
    tenants, count = paginated_tenants
    return PaginatedResults(
        count=count,
        results=[schemas.tenant.Tenant.from_orm(tenant) for tenant in tenants],
    )


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
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> schemas.tenant.Tenant:
    if tenant_create.theme_id is not None:
        theme = await theme_repository.get_by_id(tenant_create.theme_id)
        if theme is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.TENANT_CREATE_NOT_EXISTING_THEME,
            )

    slug = await repository.get_available_slug(tenant_create.name)
    tenant = Tenant(**tenant_create.dict(), slug=slug)
    tenant = await repository.create(tenant)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, tenant)

    client = Client(
        name=f"{tenant.name}'s client",
        first_party=True,
        tenant=tenant,
        redirect_uris=["http://localhost:8000/docs/oauth2-redirect"],
    )
    await client_repository.create(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, client)

    return schemas.tenant.Tenant.from_orm(tenant)


@router.patch("/{id:uuid}", name="tenants:update", response_model=schemas.tenant.Tenant)
async def update_tenant(
    tenant_update: schemas.tenant.TenantUpdate,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    theme_repository: ThemeRepository = Depends(
        get_workspace_repository(ThemeRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> schemas.tenant.Tenant:
    if tenant_update.theme_id is not None:
        theme = await theme_repository.get_by_id(tenant_update.theme_id)
        if theme is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.TENANT_UPDATE_NOT_EXISTING_THEME,
            )

    tenant_update_dict = tenant_update.dict(exclude_unset=True)
    for field, value in tenant_update_dict.items():
        setattr(tenant, field, value)

    await repository.update(tenant)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, tenant)

    return schemas.tenant.Tenant.from_orm(tenant)
