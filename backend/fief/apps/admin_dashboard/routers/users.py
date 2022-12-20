from fastapi import APIRouter, Depends, Request, status
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists

from fief import schemas
from fief.apps.admin_dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.admin_dashboard.forms.user import UserCreateForm, UserUpdateForm
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.crypto.password import password_helper
from fief.db import AsyncSession
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import (
    get_current_workspace,
    get_current_workspace_session,
)
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tasks import get_send_task
from fief.dependencies.user_field import get_user_fields
from fief.dependencies.users import (
    SQLAlchemyUserTenantDatabase,
    UserManager,
    get_admin_user_create_internal_model,
    get_admin_user_update_model,
    get_paginated_users,
    get_user_by_id_or_404,
    get_user_manager_from_user,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, User, UserField, Workspace
from fief.repositories import TenantRepository
from fief.tasks import SendTask
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_columns(
    user_fields: list[UserField] = Depends(get_user_fields),
) -> list[DatatableColumn]:
    return [
        DatatableColumn("Email address", "email", "email_column", ordering="email"),
        DatatableColumn("ID", "id", "id_column", ordering="id"),
        DatatableColumn("Tenant", "tenant", "tenant_column", ordering="tenant.name"),
        *[
            DatatableColumn(
                user_field.name,
                user_field.slug,
                "user_field_value_column",
                renderer_macro_kwargs={"user_field": user_field},
            )
            for user_field in user_fields
        ],
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["email", "id", "tenant"])
    ),
    paginated_users: PaginatedObjects[User] = Depends(get_paginated_users),
):
    users, count = paginated_users

    return {
        "users": users,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


@router.get("/", name="dashboard.users:list")
async def list_users(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/users/list.html", {**context, **list_context}
    )


@router.get("/{id:uuid}", name="dashboard.users:get")
async def get_user(
    user: User = Depends(get_user_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/users/get/account.html",
        {**context, **list_context, "user": user, "tab": "account"},
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.users:create")
async def create_user(
    request: Request,
    user_create_internal_model: type[
        schemas.user.UserCreateInternal[schemas.user.UF]
    ] = Depends(get_admin_user_create_internal_model),
    user_fields: list[UserField] = Depends(get_user_fields),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    session: AsyncSession = Depends(get_current_workspace_session),
    workspace: Workspace = Depends(get_current_workspace),
    send_task: SendTask = Depends(get_send_task),
):
    form_class = await UserCreateForm.get_form_class(user_fields)
    form_helper = FormHelper(
        form_class,
        "admin/users/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        tenant = await tenant_repository.get_by_id(form.data["tenant_id"])
        if tenant is None:
            form.tenant_id.errors.append("Unknown tenant.")
            return await form_helper.get_error_response(
                "Unknown tenant.", "unknown_tenant"
            )

        user_db = SQLAlchemyUserTenantDatabase(session, tenant, User)
        user_manager = UserManager(
            user_db, password_helper, workspace, tenant, send_task, audit_logger
        )
        user_create = user_create_internal_model(**form.data)

        try:
            user = await user_manager.create_with_fields(
                user_create, user_fields=user_fields, request=request
            )
            audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, user)
        except UserAlreadyExists:
            form.email.errors.append(
                "A user with this email address already exists on this tenant."
            )
            return await form_helper.get_error_response(
                "A user with this email address already exists on this tenant.",
                "user_already_exists",
            )
        except InvalidPasswordException as e:
            form.password.errors.append(e.reason)
            return await form_helper.get_error_response(e.reason, "invalid_password")

        return HXRedirectResponse(
            request.url_for("dashboard.users:get", id=user.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(user.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.users:update",
)
async def update_user(
    request: Request,
    user_update_model: type[schemas.user.UserUpdate[schemas.user.UF]] = Depends(
        get_admin_user_update_model
    ),
    user: User = Depends(get_user_by_id_or_404),
    user_fields: list[UserField] = Depends(get_user_fields),
    user_manager: UserManager = Depends(get_user_manager_from_user),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_class = await UserUpdateForm.get_form_class(user_fields)
    form_helper = FormHelper(
        form_class,
        "admin/users/edit.html",
        object=user,
        request=request,
        context={**context, **list_context, "user": user},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        data = form.data

        if data["password"] is None:
            data.pop("password")

        user_update = user_update_model(**data)

        try:
            user = await user_manager.update_with_fields(
                user_update, user, user_fields=user_fields, request=request
            )
            audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, user)
        except UserAlreadyExists:
            form.email.errors.append(
                "A user with this email address already exists on this tenant."
            )
            return await form_helper.get_error_response(
                "A user with this email address already exists on this tenant.",
                "user_already_exists",
            )
        except InvalidPasswordException as e:
            form.password.errors.append(e.reason)
            return await form_helper.get_error_response(e.reason, "invalid_password")

        return HXRedirectResponse(request.url_for("dashboard.users:get", id=user.id))

    return await form_helper.get_response()
