from fastapi import APIRouter, Depends, Request, status

from fief.apps.admin_dashboard.dependencies import BaseContext, get_base_context
from fief.apps.admin_dashboard.forms.api_key import APIKeyCreateForm
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.crypto.token import generate_token
from fief.dependencies.admin_api_key import (
    get_api_key_by_id_or_404,
    get_paginated_api_keys,
)
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.main_repositories import get_main_repository
from fief.dependencies.pagination import (
    PaginatedObjects,
    Pagination,
    RawOrdering,
    get_pagination,
    get_raw_ordering,
)
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AdminAPIKey, AuditLogMessage, Workspace
from fief.repositories import AdminAPIKeyRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_list_context(
    pagination: Pagination = Depends(get_pagination),
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
    paginated_api_keys: PaginatedObjects[AdminAPIKey] = Depends(get_paginated_api_keys),
):
    api_keys, count = paginated_api_keys
    limit, skip = pagination
    return {
        "api_keys": api_keys,
        "count": count,
        "limit": limit,
        "skip": skip,
        "ordering": raw_ordering,
    }


@router.get("/", name="dashboard.api_keys:list")
async def list_api_keys(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/api_keys/list.html", {**context, **list_context}
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.api_keys:create")
async def create_api_key(
    request: Request,
    current_workspace: Workspace = Depends(get_current_workspace),
    repository: AdminAPIKeyRepository = Depends(
        get_main_repository(AdminAPIKeyRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        APIKeyCreateForm,
        "admin/api_keys/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        token, token_hash = generate_token()
        api_key = AdminAPIKey(token=token_hash, workspace_id=current_workspace.id)
        form.populate_obj(api_key)

        api_key = await repository.create(api_key)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, api_key)

        return templates.TemplateResponse(
            "admin/api_keys/token.html",
            {**context, **list_context, "api_key": api_key, "token": token},
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(api_key.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete", methods=["GET", "DELETE"], name="dashboard.api_keys:delete"
)
async def delete_api_key(
    request: Request,
    api_key: AdminAPIKey = Depends(get_api_key_by_id_or_404),
    repository: AdminAPIKeyRepository = Depends(
        get_main_repository(AdminAPIKeyRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    if request.method == "DELETE":
        await repository.delete(api_key)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, api_key)

        return HXRedirectResponse(
            request.url_for("dashboard.api_keys:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            "admin/api_keys/delete.html",
            {**context, **list_context, "api_key": api_key},
        )
