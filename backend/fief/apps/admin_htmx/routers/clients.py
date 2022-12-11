from fastapi import APIRouter, Depends, Request

from fief.apps.admin_htmx.dependencies import BaseContext, get_base_context
from fief.apps.admin_htmx.forms.client import ClientCreateForm
from fief.apps.admin_htmx.responses import HXRedirectResponse
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.client import get_client_by_id_or_404, get_paginated_clients
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import (
    PaginatedObjects,
    Pagination,
    RawOrdering,
    get_pagination,
    get_raw_ordering,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Client
from fief.repositories import ClientRepository, TenantRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_list_context(
    pagination: Pagination = Depends(get_pagination),
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
):
    clients, count = paginated_clients
    limit, skip = pagination
    return {
        "clients": clients,
        "count": count,
        "limit": limit,
        "skip": skip,
        "ordering": raw_ordering,
    }


@router.get("/", name="dashboard:clients:list")
async def list_clients(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/clients/list.html", {**context, **list_context}
    )


@router.get("/{id:uuid}", name="dashboard:clients:get")
async def get_client(
    client: Client = Depends(get_client_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/clients/get.html",
        {**context, **list_context, "client": client},
    )


@router.api_route(
    "/create",
    methods=["GET", "POST"],
    name="dashboard:clients:create",
)
async def create_client(
    request: Request,
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        ClientCreateForm,
        "admin/clients/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        data = form.data
        data.pop("csrf_token")

        tenant = await tenant_repository.get_by_id(data["tenant_id"])
        if tenant is None:
            form.tenant_id.errors.append("Unknown tenant.")
            return await form_helper.get_error_response(
                "Unknown tenant.", "unknown_tenant"
            )

        client = Client(**data)
        client = await repository.create(client)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, client)

        return HXRedirectResponse(
            request.url_for("dashboard:clients:get", id=client.id)
        )

    return await form_helper.get_response()
