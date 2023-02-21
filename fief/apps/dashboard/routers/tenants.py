from fastapi import APIRouter, Depends, Header, Request, status

from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.tenant import TenantCreateForm, TenantUpdateForm
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tenant import get_paginated_tenants, get_tenant_by_id_or_404
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client, OAuthProvider, Tenant
from fief.repositories import (
    ClientRepository,
    OAuthProviderRepository,
    TenantRepository,
    ThemeRepository,
)
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


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
    theme_repository: ThemeRepository = Depends(
        get_workspace_repository(ThemeRepository)
    ),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
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

        theme_id = form.data["theme"]
        if theme_id is not None:
            theme = await theme_repository.get_by_id(theme_id)
            if theme is None:
                form.theme.errors.append("Unknown theme.")
                return await form_helper.get_error_response(
                    "Unknown theme.", "unknown_theme"
                )
            form.theme.data = theme

        oauth_providers_ids = form.data["oauth_providers"]
        oauth_providers: list[OAuthProvider] = []
        for oauth_provider_id in oauth_providers_ids:
            oauth_provider = await oauth_provider_repository.get_by_id(
                oauth_provider_id
            )
            if oauth_provider is None:
                form.oauth_providers.errors.append("Unknown OAuth Provider.")
                return await form_helper.get_error_response(
                    "Unknown OAuth Provider.", "unknown_oauth_provider"
                )
            oauth_providers.append(oauth_provider)
            form.oauth_providers.data = oauth_providers

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
    theme_repository: ThemeRepository = Depends(
        get_workspace_repository(ThemeRepository)
    ),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
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
    form = await form_helper.get_form()
    form.oauth_providers.choices = [
        (oauth_provider.id, oauth_provider.display_name)
        for oauth_provider in tenant.oauth_providers
    ]

    if await form_helper.is_submitted_and_valid():
        theme_id = form.data["theme"]
        if theme_id is not None:
            theme = await theme_repository.get_by_id(theme_id)
            if theme is None:
                form.theme.errors.append("Unknown theme.")
                return await form_helper.get_error_response(
                    "Unknown theme.", "unknown_theme"
                )
            form.theme.data = theme

        tenant.oauth_providers = []
        for oauth_provider_id in form.data["oauth_providers"]:
            oauth_provider = await oauth_provider_repository.get_by_id(
                oauth_provider_id
            )
            if oauth_provider is None:
                form.oauth_providers.errors.append("Unknown OAuth Provider.")
                return await form_helper.get_error_response(
                    "Unknown OAuth Provider.", "unknown_oauth_provider"
                )
            tenant.oauth_providers.append(oauth_provider)

        del form.oauth_providers
        form.populate_obj(tenant)

        await repository.update(tenant)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, tenant)

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:get", id=tenant.id)
        )

    return await form_helper.get_response()
