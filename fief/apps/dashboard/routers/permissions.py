from fastapi import APIRouter, Depends, Header, Request, status

from fief import schemas
from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.permission import PermissionCreateForm
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.permission import (
    get_paginated_permissions,
    get_permission_by_id_or_404,
)
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Permission
from fief.repositories import PermissionRepository
from fief.services.webhooks.models import (
    PermissionCreated,
    PermissionDeleted,
)
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Name", "name", "name_column", ordering="name"),
        DatatableColumn("Codename", "codename", "codename_column", ordering="codename"),
        DatatableColumn("Actions", "actions", "actions_column"),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["name", "codename", "actions"])
    ),
    paginated_permissions: PaginatedObjects[Permission] = Depends(
        get_paginated_permissions
    ),
):
    permissions, count = paginated_permissions
    return {
        "permissions": permissions,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/permissions/list_combobox.html"
    return "admin/permissions/list.html"


async def get_form_helper(
    request: Request,
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
) -> FormHelper[PermissionCreateForm]:
    form_helper = FormHelper(
        PermissionCreateForm,
        template,
        request=request,
        context={**context, **list_context},
    )
    await form_helper.get_form()
    return form_helper


@router.api_route("/", methods=["GET", "POST"], name="dashboard.permissions:list")
async def list_permissions(
    request: Request,
    form_helper: FormHelper[PermissionCreateForm] = Depends(get_form_helper),
    repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        existing_permission = await repository.get_by_codename(form.data["codename"])
        if existing_permission is not None:
            form.codename.errors.append(
                "A permission already exists with this codename. A codename must be unique within your workspace."
            )
            return await form_helper.get_error_response(
                "A permission already exists with this codename. A codename must be unique within your workspace.",
                "permission_codename_already_exists",
            )

        permission = Permission()
        form.populate_obj(permission)
        permission = await repository.create(permission)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, permission)
        trigger_webhooks(PermissionCreated, permission, schemas.permission.Permission)

        return HXRedirectResponse(
            request.url_for("dashboard.permissions:list"),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(permission.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete", methods=["GET", "DELETE"], name="dashboard.permissions:delete"
)
async def delete_permission(
    request: Request,
    form_helper: FormHelper[PermissionCreateForm] = Depends(get_form_helper),
    permission: Permission = Depends(get_permission_by_id_or_404),
    repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    if request.method == "DELETE":
        await repository.delete(permission)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, permission)
        trigger_webhooks(PermissionDeleted, permission, schemas.permission.Permission)

        return HXRedirectResponse(
            request.url_for("dashboard.permissions:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            request,
            "admin/permissions/delete.html",
            {**form_helper.context, "permission": permission},
        )
