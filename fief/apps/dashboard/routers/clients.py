import secrets

from fastapi import APIRouter, Depends, Header, Request, status

from fief import schemas
from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.client import (
    ClientCreateForm,
    ClientLifetimesForm,
    ClientUpdateForm,
)
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.crypto.jwk import generate_jwk
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client
from fief.repositories import ClientRepository, TenantRepository
from fief.services.webhooks.models import ClientCreated, ClientUpdated
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Name", "name", "name_column", ordering="name"),
        DatatableColumn("Type", "type", "type_column", ordering="client_type"),
        DatatableColumn("Tenant", "tenant", "tenant_column", ordering="tenant.name"),
        DatatableColumn(
            "Client ID", "client_id", "client_id_column", ordering="client_id"
        ),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["name", "type", "tenant", "client_id"])
    ),
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
):
    clients, count = paginated_clients
    return {
        "clients": clients,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/clients/list_combobox.html"
    return "admin/clients/list.html"


@router.get("/", name="dashboard.clients:list")
async def list_clients(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})


@router.get("/{id:uuid}", name="dashboard.clients:get")
async def get_client(
    client: Client = Depends(get_client_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/clients/get/general.html",
        {**context, **list_context, "client": client, "tab": "general"},
    )


@router.api_route(
    "/{id:uuid}/lifetimes", methods=["GET", "POST"], name="dashboard.clients:lifetimes"
)
async def client_lifetimes(
    request: Request,
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    client: Client = Depends(get_client_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        ClientLifetimesForm,
        "admin/clients/get/lifetimes.html",
        object=client,
        request=request,
        context={**context, **list_context, "client": client, "tab": "lifetimes"},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(client)

        await repository.update(client)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)
        trigger_webhooks(ClientUpdated, client, schemas.client.Client)

        return HXRedirectResponse(
            request.url_for("dashboard.clients:lifetimes", id=client.id)
        )

    return await form_helper.get_response()


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.clients:create")
async def create_client(
    request: Request,
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        ClientCreateForm,
        "admin/clients/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        tenant = await tenant_repository.get_by_id(form.data["tenant"])
        if tenant is None:
            form.tenant.errors.append("Unknown tenant.")
            return await form_helper.get_error_response(
                "Unknown tenant.", "unknown_tenant"
            )
        form.tenant.data = tenant

        client = Client()
        form.populate_obj(client)
        client = await repository.create(client)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, client)
        trigger_webhooks(ClientCreated, client, schemas.client.Client)

        return HXRedirectResponse(
            request.url_for("dashboard.clients:get", id=client.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(client.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.clients:update",
)
async def update_client(
    request: Request,
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        ClientUpdateForm,
        "admin/clients/edit.html",
        object=client,
        request=request,
        context={**context, **list_context, "client": client},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(client)

        await repository.update(client)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)
        trigger_webhooks(ClientUpdated, client, schemas.client.Client)

        return HXRedirectResponse(
            request.url_for("dashboard.clients:get", id=client.id)
        )

    return await form_helper.get_response()


@router.post(
    "/{id:uuid}/encryption-key",
    name="dashboard.clients:encryption_key",
)
async def create_encryption_key(
    client: Client = Depends(get_client_by_id_or_404),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    client.encrypt_jwk = key.export_public()
    await repository.update(client)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, client)
    trigger_webhooks(ClientUpdated, client, schemas.client.Client)

    return templates.TemplateResponse(
        "admin/clients/encryption_key.html",
        {**context, "client": client, "key": key.export(as_dict=True)},
    )
