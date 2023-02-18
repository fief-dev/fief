from fastapi import APIRouter, Depends, Header, Request, status

from fief.apps.admin_dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.admin_dashboard.forms.oauth_provider import (
    OAuthProviderCreateForm,
    OAuthProviderUpdateForm,
)
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.oauth_provider import (
    get_oauth_provider_by_id_or_404,
    get_paginated_oauth_providers,
)
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, OAuthProvider
from fief.repositories import OAuthProviderRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Provider", "provider", "provider_column", ordering="provider"),
        DatatableColumn("Name", "name", "name_column", ordering="name"),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["provider", "name"])
    ),
    paginated_oauth_providers: PaginatedObjects[OAuthProvider] = Depends(
        get_paginated_oauth_providers
    ),
):
    oauth_providers, count = paginated_oauth_providers
    return {
        "oauth_providers": oauth_providers,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/oauth_providers/list_combobox.html"
    return "admin/oauth_providers/list.html"


@router.get("/", name="dashboard.oauth_providers:list")
async def list_oauth_providers(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})


@router.get("/{id:uuid}", name="dashboard.oauth_providers:get")
async def get_oauth_provider(
    oauth_provider: OAuthProvider = Depends(get_oauth_provider_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/oauth_providers/get.html",
        {**context, **list_context, "oauth_provider": oauth_provider},
    )


@router.api_route(
    "/create", methods=["GET", "POST"], name="dashboard.oauth_providers:create"
)
async def create_oauth_provider(
    request: Request,
    hx_trigger: str | None = Header(None),
    repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        OAuthProviderCreateForm,
        "admin/oauth_providers/create.html",
        request=request,
        context={**context, **list_context},
    )

    if hx_trigger is None and await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        oauth_provider = OAuthProvider()
        form.populate_obj(oauth_provider)
        oauth_provider = await repository.create(oauth_provider)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, oauth_provider)

        return HXRedirectResponse(
            request.url_for("dashboard.oauth_providers:get", id=oauth_provider.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(oauth_provider.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.oauth_providers:update",
)
async def update_oauth_provider(
    request: Request,
    oauth_provider: OAuthProvider = Depends(get_oauth_provider_by_id_or_404),
    repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        OAuthProviderUpdateForm,
        "admin/oauth_providers/edit.html",
        object=oauth_provider,
        request=request,
        context={**context, **list_context, "oauth_provider": oauth_provider},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(oauth_provider)

        await repository.update(oauth_provider)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, oauth_provider)

        return HXRedirectResponse(
            request.url_for("dashboard.oauth_providers:get", id=oauth_provider.id)
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete",
    methods=["GET", "DELETE"],
    name="dashboard.oauth_providers:delete",
)
async def delete_oauth_provider(
    request: Request,
    oauth_provider: OAuthProvider = Depends(get_oauth_provider_by_id_or_404),
    repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    if request.method == "DELETE":
        await repository.delete(oauth_provider)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, oauth_provider)

        return HXRedirectResponse(
            request.url_for("dashboard.oauth_providers:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            "admin/oauth_providers/delete.html",
            {**context, **list_context, "oauth_provider": oauth_provider},
        )
