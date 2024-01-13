from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from fief import schemas
from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.tenant import (
    TenantCreateForm,
    TenantEmailForm,
    TenantUpdateForm,
)
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.email_provider import get_email_provider
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.repositories import get_repository
from fief.dependencies.tenant import get_paginated_tenants, get_tenant_by_id_or_404
from fief.dependencies.tenant_email_domain import get_tenant_email_domain
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client, OAuthProvider, Tenant
from fief.repositories import (
    ClientRepository,
    OAuthProviderRepository,
    TenantRepository,
    ThemeRepository,
    UserRepository,
)
from fief.services.email import EmailProvider
from fief.services.tenant_email_domain import (
    DomainAuthenticationNotImplementedError,
    TenantEmailDomain,
    TenantEmailDomainError,
)
from fief.services.webhooks.models import (
    ClientCreated,
    TenantCreated,
    TenantDeleted,
    TenantUpdated,
)
from fief.settings import settings
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
    request: Request,
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(request, template, {**context, **list_context})


@router.get("/{id:uuid}", name="dashboard.tenants:get")
async def get_tenant(
    request: Request,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        request,
        "admin/tenants/get/general.html",
        {**context, **list_context, "tenant": tenant, "tab": "general"},
    )


@router.api_route(
    "/{id:uuid}/email", methods=["GET", "POST"], name="dashboard.tenants:email"
)
async def tenant_email(
    request: Request,
    repository: TenantRepository = Depends(TenantRepository),
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    tenant_email_domain: TenantEmailDomain = Depends(get_tenant_email_domain),
    email_provider: EmailProvider = Depends(get_email_provider),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        TenantEmailForm,
        "admin/tenants/get/email.html",
        object=tenant,
        request=request,
        context={
            **context,
            **list_context,
            "tenant": tenant,
            "tab": "email",
            "email_provider": email_provider,
            "default_from_name": settings.default_from_name,
            "default_from_email": settings.default_from_email,
        },
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(tenant)

        if tenant.email_from_email is not None:
            try:
                tenant = await tenant_email_domain.authenticate_domain(tenant)
            except DomainAuthenticationNotImplementedError:
                pass
            except TenantEmailDomainError as e:
                return await form_helper.get_error_response(
                    e.message, "tenant_email_domain_error"
                )

        await repository.update(tenant)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, tenant)
        trigger_webhooks(TenantUpdated, tenant, schemas.tenant.Tenant)

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:email", id=tenant.id)
        )

    return await form_helper.get_response()


@router.get(
    "/{id:uuid}/email/domain", name="dashboard.tenants:email_domain_authentication"
)
async def tenant_email_domain_authentication(
    request: Request,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    email_provider: EmailProvider = Depends(get_email_provider),
):
    if tenant.email_domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    form_helper = FormHelper(
        TenantEmailForm,
        "admin/tenants/get/email_domain_authentication.html",
        object=tenant,
        request=request,
        context={
            **context,
            **list_context,
            "tenant": tenant,
            "tab": "email",
            "email_provider": email_provider,
            "default_from_name": settings.default_from_name,
            "default_from_email": settings.default_from_email,
        },
    )
    return await form_helper.get_response()


@router.post("/{id:uuid}/email/verify", name="dashboard.tenants:email_domain_verify")
async def tenant_email_domain_verify(
    request: Request,
    hx_request: bool = Header(False),
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    tenant_email_domain: TenantEmailDomain = Depends(get_tenant_email_domain),
):
    if tenant.email_domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        tenant = await tenant_email_domain.verify_domain(tenant)
    except TenantEmailDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e

    redirect_url = request.url_for(
        "dashboard.tenants:email_domain_authentication", id=tenant.id
    )

    if hx_request:
        return HXRedirectResponse(redirect_url)
    else:
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.tenants:create")
async def create_tenant(
    request: Request,
    repository: TenantRepository = Depends(TenantRepository),
    client_repository: ClientRepository = Depends(ClientRepository),
    theme_repository: ThemeRepository = Depends(ThemeRepository),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_repository(OAuthProviderRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
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
    repository: TenantRepository = Depends(TenantRepository),
    theme_repository: ThemeRepository = Depends(ThemeRepository),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_repository(OAuthProviderRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
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
        trigger_webhooks(TenantUpdated, tenant, schemas.tenant.Tenant)

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:get", id=tenant.id)
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete",
    methods=["GET", "DELETE"],
    name="dashboard.tenants:delete",
)
async def delete_tenant(
    request: Request,
    tenant: Tenant = Depends(get_tenant_by_id_or_404),
    repository: TenantRepository = Depends(TenantRepository),
    user_repository: UserRepository = Depends(UserRepository),
    client_repository: ClientRepository = Depends(ClientRepository),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    if request.method == "DELETE":
        await repository.delete(tenant)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, tenant)
        trigger_webhooks(TenantDeleted, tenant, schemas.tenant.Tenant)

        return HXRedirectResponse(
            request.url_for("dashboard.tenants:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )

    users_count = await user_repository.count_by_tenant(tenant.id)
    clients_count = await client_repository.count_by_tenant(tenant.id)
    return templates.TemplateResponse(
        request,
        "admin/tenants/delete.html",
        {
            **context,
            **list_context,
            "tenant": tenant,
            "users_count": users_count,
            "clients_count": clients_count,
        },
    )
