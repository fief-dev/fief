from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import UUID4

from fief import schemas, tasks
from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.user import (
    CreateUserPermissionForm,
    CreateUserRoleForm,
    UserAccessTokenForm,
    UserCreateForm,
    UserUpdateForm,
)
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.crypto.access_token import generate_access_token
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.permission import (
    UserPermissionsGetter,
    get_user_permissions_getter,
)
from fief.dependencies.tasks import get_send_task
from fief.dependencies.tenant import get_tenants
from fief.dependencies.user_field import get_user_create_admin_model, get_user_fields
from fief.dependencies.users import (
    get_admin_user_update_model,
    get_paginated_users,
    get_user_by_id_or_404,
    get_user_manager,
    get_user_oauth_accounts,
    get_user_permissions,
    get_user_roles,
)
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import (
    AuditLogMessage,
    OAuthAccount,
    Tenant,
    User,
    UserField,
    UserPermission,
    UserRole,
)
from fief.repositories import (
    ClientRepository,
    PermissionRepository,
    RoleRepository,
    TenantRepository,
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.services.acr import ACR
from fief.services.user_manager import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserManager,
)
from fief.services.webhooks.models import (
    UserDeleted,
    UserPermissionCreated,
    UserPermissionDeleted,
    UserRoleCreated,
    UserRoleDeleted,
)
from fief.tasks import SendTask
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns(
    user_fields: list[UserField] = Depends(get_user_fields),
) -> list[DatatableColumn]:
    return [
        DatatableColumn("Email address", "email", "email_column", ordering="email"),
        DatatableColumn(
            "Email verified",
            "email_verified",
            "email_verified_column",
            ordering="email_verified",
        ),
        DatatableColumn(
            "Created at", "created_at", "created_at_column", ordering="created_at"
        ),
        DatatableColumn(
            "Updated at", "updated_at", "updated_at_column", ordering="updated_at"
        ),
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
        DatatableQueryParametersGetter(
            ["email", "email_verified", "created_at", "id", "tenant"],
            ["tenant", "query"],
        )
    ),
    paginated_users: PaginatedObjects[User] = Depends(get_paginated_users),
    tenants: list[Tenant] = Depends(get_tenants),
):
    users, count = paginated_users

    return {
        "users": users,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
        "tenants": tenants,
    }


@router.get("/", name="dashboard.users:list")
async def list_users(
    request: Request,
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        request, "admin/users/list.html", {**context, **list_context}
    )


@router.get("/{id:uuid}", name="dashboard.users:get")
async def get_user(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        request,
        "admin/users/get/account.html",
        {**context, **list_context, "user": user, "tab": "account"},
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.users:create")
async def create_user(
    request: Request,
    user_create_admin_model: type[
        schemas.user.UserCreateAdmin[schemas.user.UF]
    ] = Depends(get_user_create_admin_model),
    user_fields: list[UserField] = Depends(get_user_fields),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    user_manager: UserManager = Depends(get_user_manager),
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

        tenant = await tenant_repository.get_by_id(form.data["tenant"])
        if tenant is None:
            form.tenant.errors.append("Unknown tenant.")
            return await form_helper.get_error_response(
                "Unknown tenant.", "unknown_tenant"
            )

        user_create = user_create_admin_model(**form.data, tenant_id=tenant.id)

        try:
            user = await user_manager.create(user_create, tenant.id, request=request)
            audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, user)
        except UserAlreadyExistsError:
            form.email.errors.append(
                "A user with this email address already exists on this tenant."
            )
            return await form_helper.get_error_response(
                "A user with this email address already exists on this tenant.",
                "user_already_exists",
            )
        except InvalidPasswordError as e:
            for message in e.messages:
                form.password.errors.append(message)
            return await form_helper.get_error_response(
                ", ".join(map(str, e.messages)), "invalid_password"
            )

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
    user_update_model: type[schemas.user.UserUpdateAdmin[schemas.user.UF]] = Depends(
        get_admin_user_update_model
    ),
    user: User = Depends(get_user_by_id_or_404),
    user_fields: list[UserField] = Depends(get_user_fields),
    user_manager: UserManager = Depends(get_user_manager),
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
            user = await user_manager.update(user_update, user, request=request)
            audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, user)
        except UserAlreadyExistsError:
            form.email.errors.append(
                "A user with this email address already exists on this tenant."
            )
            return await form_helper.get_error_response(
                "A user with this email address already exists on this tenant.",
                "user_already_exists",
            )
        except InvalidPasswordError as e:
            for message in e.messages:
                form.password.errors.append(message)
            return await form_helper.get_error_response(
                ", ".join(map(str, e.messages)), "invalid_password"
            )

        return HXRedirectResponse(request.url_for("dashboard.users:get", id=user.id))

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/access-token",
    methods=["GET", "POST"],
    name="dashboard.users:access_token",
)
async def create_user_access_token(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    get_user_permissions: UserPermissionsGetter = Depends(get_user_permissions_getter),
    client_repository: ClientRepository = Depends(
        get_workspace_repository(ClientRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        UserAccessTokenForm,
        "admin/users/access_token.html",
        request=request,
        context={**context, **list_context, "user": user},
    )
    form = await form_helper.get_form()
    form.client.query_endpoint_path = f"/admin/clients?tenant={user.tenant_id}"

    if await form_helper.is_submitted_and_valid():
        data = form.data
        tenant = user.tenant

        client = await client_repository.get_by_id(data["client"])
        if client is None or client.tenant_id != tenant.id:
            form.client.errors.append("Unknown client.")
            return await form_helper.get_error_response(
                "Unknown client.", "unknown_client"
            )
        form.client.data = client

        tenant_host = tenant.get_host()
        permissions = await get_user_permissions(user)

        access_token = generate_access_token(
            user.tenant.get_sign_jwk(),
            tenant_host,
            client,
            datetime.now(UTC),
            ACR.LEVEL_ZERO,
            user,
            data["scopes"],
            permissions,
            client.access_id_token_lifetime_seconds,
        )

        audit_logger(
            AuditLogMessage.USER_TOKEN_GENERATED_BY_ADMIN,
            subject_user_id=user.id,
            scope=data["scopes"],
        )

        return templates.TemplateResponse(
            request,
            "admin/users/access_token_result.html",
            {
                **context,
                **list_context,
                "user": user,
                "access_token": access_token,
                "expires_in": client.access_id_token_lifetime_seconds,
            },
        )

    return await form_helper.get_response()


@router.post("/{id:uuid}/verify-request", name="dashboard.users:verify_email_request")
async def verify_email_request(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    user_manager: UserManager = Depends(get_user_manager),
    context: BaseContext = Depends(get_base_context),
):
    if not user.email_verified:
        await user_manager.request_verify_email(user, user.email)

    return templates.TemplateResponse(
        request,
        "admin/users/get/verify_email_requested.html",
        {**context, "user": user},
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.api_route(
    "/{id:uuid}/delete",
    methods=["GET", "DELETE"],
    name="dashboard.users:delete",
)
async def delete_user(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    repository: UserRepository = Depends(get_workspace_repository(UserRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    if request.method == "DELETE":
        await repository.delete(user)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, user)
        trigger_webhooks(UserDeleted, user, schemas.user.UserRead)

        return HXRedirectResponse(
            request.url_for("dashboard.users:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            request,
            "admin/users/delete.html",
            {**context, **list_context, "user": user},
        )


@router.api_route(
    "/{id:uuid}/permissions",
    methods=["GET", "POST"],
    name="dashboard.users:permissions",
)
async def user_permissions(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    user_permissions: list[UserPermission] = Depends(get_user_permissions),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    permission_repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    user_permission_repository: UserPermissionRepository = Depends(
        get_workspace_repository(UserPermissionRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        CreateUserPermissionForm,
        "admin/users/get/permissions.html",
        request=request,
        context={
            **context,
            **list_context,
            "user": user,
            "user_permissions": user_permissions,
            "tab": "permissions",
        },
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        permission_id = form.data["permission"]

        permission = await permission_repository.get_by_id(permission_id)
        if permission is None:
            form.permission.errors.append("Unknown permission.")
            return await form_helper.get_error_response(
                "Unknown permission.", "unknown_permission"
            )

        existing_user_permission = (
            await user_permission_repository.get_by_permission_and_user(
                user.id, permission_id, direct_only=True
            )
        )
        if existing_user_permission is not None:
            form.permission.errors.append(
                "This permission is already granted to this user."
            )
            return await form_helper.get_error_response(
                "This permission is already granted to this user.",
                "already_added_permission",
            )

        user_permission = UserPermission(user_id=user.id, permission=permission)
        await user_permission_repository.create(user_permission)
        audit_logger.log_object_write(
            AuditLogMessage.OBJECT_CREATED,
            user_permission,
            subject_user_id=user.id,
            permission_id=str(permission.id),
        )
        trigger_webhooks(
            UserPermissionCreated,
            user_permission,
            schemas.user_permission.UserPermission,
        )

        return HXRedirectResponse(
            request.url_for("dashboard.users:permissions", id=user.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(user_permission.id)},
        )

    return await form_helper.get_response()


@router.delete(
    "/{id:uuid}/permissions/{permission_id:uuid}",
    name="dashboard.users:delete_permission",
)
async def delete_user_permission(
    request: Request,
    permission_id: UUID4,
    user: User = Depends(get_user_by_id_or_404),
    user_permission_repository: UserPermissionRepository = Depends(
        get_workspace_repository(UserPermissionRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    user_permission = await user_permission_repository.get_by_permission_and_user(
        user.id, permission_id, direct_only=True
    )
    if user_permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await user_permission_repository.delete(user_permission)
    audit_logger.log_object_write(
        AuditLogMessage.OBJECT_DELETED,
        user_permission,
        subject_user_id=user.id,
        permission_id=str(permission_id),
    )
    trigger_webhooks(
        UserPermissionDeleted,
        user_permission,
        schemas.user_permission.UserPermission,
    )

    return HXRedirectResponse(
        request.url_for("dashboard.users:permissions", id=user.id),
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.api_route(
    "/{id:uuid}/roles", methods=["GET", "POST"], name="dashboard.users:roles"
)
async def user_roles(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    user_roles: list[UserRole] = Depends(get_user_roles),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    role_repository: RoleRepository = Depends(get_workspace_repository(RoleRepository)),
    user_role_repository: UserRoleRepository = Depends(
        get_workspace_repository(UserRoleRepository)
    ),
    send_task: SendTask = Depends(get_send_task),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        CreateUserRoleForm,
        "admin/users/get/roles.html",
        request=request,
        context={
            **context,
            **list_context,
            "user": user,
            "user_roles": user_roles,
            "tab": "roles",
        },
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        role_id = form.data["role"]

        role = await role_repository.get_by_id(role_id)
        if role is None:
            form.role.errors.append("Unknown role.")
            return await form_helper.get_error_response("Unknown role.", "unknown_role")

        existing_user_role = await user_role_repository.get_by_role_and_user(
            user.id, role_id
        )
        if existing_user_role is not None:
            form.role.errors.append("This role is already granted to this user.")
            return await form_helper.get_error_response(
                "This role is already granted to this user.", "already_added_role"
            )

        user_role = UserRole(user_id=user.id, role=role)
        await user_role_repository.create(user_role)
        audit_logger.log_object_write(
            AuditLogMessage.OBJECT_CREATED,
            user_role,
            subject_user_id=user.id,
            role_id=str(role.id),
        )
        trigger_webhooks(UserRoleCreated, user_role, schemas.user_role.UserRole)

        send_task(tasks.on_user_role_created, str(user.id), str(role.id))

        return HXRedirectResponse(
            request.url_for("dashboard.users:roles", id=user.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(user_role.id)},
        )

    return await form_helper.get_response()


@router.delete("/{id:uuid}/roles/{role_id:uuid}", name="dashboard.users:delete_role")
async def delete_user_role(
    request: Request,
    role_id: UUID4,
    user: User = Depends(get_user_by_id_or_404),
    user_role_repository: UserRoleRepository = Depends(
        get_workspace_repository(UserRoleRepository)
    ),
    send_task: SendTask = Depends(get_send_task),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    user_role = await user_role_repository.get_by_role_and_user(user.id, role_id)
    if user_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await user_role_repository.delete(user_role)
    audit_logger.log_object_write(
        AuditLogMessage.OBJECT_DELETED,
        user_role,
        subject_user_id=user.id,
        role_id=str(role_id),
    )
    trigger_webhooks(UserRoleDeleted, user_role, schemas.user_role.UserRole)

    send_task(tasks.on_user_role_deleted, str(user.id), str(role_id))

    return HXRedirectResponse(
        request.url_for("dashboard.users:roles", id=user.id),
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get("/{id:uuid}/oauth-accounts", name="dashboard.users:oauth_accounts")
async def user_oauth_accounts(
    request: Request,
    user: User = Depends(get_user_by_id_or_404),
    oauth_accounts: list[OAuthAccount] = Depends(get_user_oauth_accounts),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        request,
        "admin/users/get/oauth_accounts.html",
        {
            **context,
            **list_context,
            "user": user,
            "oauth_accounts": oauth_accounts,
            "tab": "oauth",
        },
    )
