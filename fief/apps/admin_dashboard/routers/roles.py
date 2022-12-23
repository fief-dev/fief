from fastapi import APIRouter, Depends, Header, Request, status

from fief.apps.admin_dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.admin_dashboard.forms.role import RoleCreateForm, RoleUpdateForm
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.role import get_paginated_roles, get_role_by_id_or_404
from fief.dependencies.tasks import get_send_task
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Role, Workspace
from fief.repositories import PermissionRepository, RoleRepository
from fief.tasks import SendTask, on_role_updated
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Name", "name", "name_column", ordering="name"),
        DatatableColumn(
            "Granted by default",
            "granted_by_default",
            "granted_by_default_column",
            ordering="granted_by_default",
        ),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["name", "granted_by_default"])
    ),
    paginated_roles: PaginatedObjects[Role] = Depends(get_paginated_roles),
):
    roles, count = paginated_roles
    return {
        "roles": roles,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/roles/list_combobox.html"
    return "admin/roles/list.html"


@router.get("/", name="dashboard.roles:list")
async def list_roles(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})


@router.get("/{id:uuid}", name="dashboard.roles:get")
async def get_role(
    role: Role = Depends(get_role_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/roles/get.html",
        {**context, **list_context, "role": role},
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.roles:create")
async def create_role(
    request: Request,
    repository: RoleRepository = Depends(get_workspace_repository(RoleRepository)),
    permission_repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        RoleCreateForm,
        "admin/roles/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        role = Role()
        form.populate_obj(role)
        role.permissions = []
        for permission_id in form.data["permissions"]:
            permission = await permission_repository.get_by_id(permission_id)
            if permission is None:
                form.permissions.errors.append("Unknown permission.")
                return await form_helper.get_error_response(
                    "Unknown permission.", "unknown_permission"
                )
            role.permissions.append(permission)

        role = await repository.create(role)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, role)

        return HXRedirectResponse(
            request.url_for("dashboard.roles:get", id=role.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(role.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.roles:update",
)
async def update_role(
    request: Request,
    role: Role = Depends(get_role_by_id_or_404),
    repository: RoleRepository = Depends(get_workspace_repository(RoleRepository)),
    permission_repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    send_task: SendTask = Depends(get_send_task),
    workspace: Workspace = Depends(get_current_workspace),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        RoleUpdateForm,
        "admin/roles/edit.html",
        object=role,
        request=request,
        context={**context, **list_context, "role": role},
    )
    form = await form_helper.get_form()
    form.permissions.choices = [
        (permission.id, permission.codename) for permission in role.permissions
    ]

    if await form_helper.is_submitted_and_valid():
        old_permissions = {permission.id for permission in role.permissions}

        role.permissions = []
        for permission_id in form.data["permissions"]:
            permission = await permission_repository.get_by_id(permission_id)
            if permission is None:
                form.permissions.errors.append("Unknown permission.")
                return await form_helper.get_error_response(
                    "Unknown permission.", "unknown_permission"
                )
            role.permissions.append(permission)
        new_permissions = {permission.id for permission in role.permissions}

        del form.permissions
        form.populate_obj(role)

        await repository.update(role)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, role)

        added_permissions = new_permissions - old_permissions
        deleted_permissions = old_permissions - new_permissions
        send_task(
            on_role_updated,
            str(role.id),
            list(map(str, added_permissions)),
            list(map(str, deleted_permissions)),
            str(workspace.id),
        )

        return HXRedirectResponse(request.url_for("dashboard.roles:get", id=role.id))

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete",
    methods=["GET", "DELETE"],
    name="dashboard.roles:delete",
)
async def delete_role(
    request: Request,
    role: Role = Depends(get_role_by_id_or_404),
    repository: RoleRepository = Depends(get_workspace_repository(RoleRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    if request.method == "DELETE":
        await repository.delete(role)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, role)

        return HXRedirectResponse(
            request.url_for("dashboard.roles:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            "admin/roles/delete.html",
            {**context, **list_context, "role": role},
        )
