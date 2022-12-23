from fastapi import APIRouter, Depends, Header, Request, status

from fief.apps.admin_dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.admin_dashboard.forms.tenant import TenantCreateForm, TenantUpdateForm
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tenant import get_paginated_tenants, get_tenant_by_id_or_404
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client, Tenant
from fief.repositories import ClientRepository, TenantRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Name", "name", "name_column", ordering="name"),
        DatatableColumn("Base URL", "base_url", "base_url_column"),
        DatatableColumn(
            "Registration allowed",
            "registration_allowed",
            "registration_allowed_column",
            ordering="registration_allowed",
        ),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["name", "base_url", "registration_allowed"])
    ),
    paginated_tenants: PaginatedObjects[Tenant] = Depends(get_paginated_tenants),
):
    tenants, count = paginated_tenants
    return {
        "tenants": tenants,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/tenants/list_combobox.html"
    return "admin/tenants/list.html"


@router.get("/", name="dashboard.tenants:list")
async def list_tenants(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})


@router.get("/{id:uuid}", name="dashboard.tenants:get")
async def get_tenant(
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/tenants/get.html",
        {**context, **list_context, "tenant": tenant},
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.tenants:create")
async def create_tenant(
    request: Request,
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    client_repository: ClientRepository = Depends(
        get_workspace_repository(ClientRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        TenantCreateForm,
        "admin/tenants/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        tenant = Tenant()
        form.populate_obj(tenant)
        tenant.slug = await repository.get_available_slug(tenant.name)
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

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:get", id=tenant.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(tenant.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.tenants:update",
)
async def update_tenant(
    request: Request,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        TenantUpdateForm,
        "admin/tenants/edit.html",
        object=tenant,
        request=request,
        context={**context, **list_context, "tenant": tenant},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(tenant)

        await repository.update(tenant)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, tenant)

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:get", id=tenant.id)
        )

    return await form_helper.get_response()
