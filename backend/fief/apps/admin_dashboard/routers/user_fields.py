from fastapi import APIRouter, Depends, Header, Request, status

from fief.apps.admin_dashboard.dependencies import BaseContext, get_base_context
from fief.apps.admin_dashboard.forms.user_field import (
    UserFieldConfigurationBase,
    UserFieldCreateForm,
    UserFieldUpdateForm,
)
from fief.apps.admin_dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import (
    PaginatedObjects,
    Pagination,
    RawOrdering,
    get_pagination,
    get_raw_ordering,
)
from fief.dependencies.user_field import (
    get_paginated_user_fields,
    get_user_field_by_id_or_404,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, OAuthProvider, UserField
from fief.repositories import UserFieldRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_list_context(
    pagination: Pagination = Depends(get_pagination),
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
    paginated_user_fields: PaginatedObjects[OAuthProvider] = Depends(
        get_paginated_user_fields
    ),
):
    user_fields, count = paginated_user_fields
    limit, skip = pagination
    return {
        "user_fields": user_fields,
        "count": count,
        "limit": limit,
        "skip": skip,
        "ordering": raw_ordering,
    }


@router.get("/", name="dashboard.user_fields:list")
async def list_user_fields(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/user_fields/list.html", {**context, **list_context}
    )


@router.get("/{id:uuid}", name="dashboard.user_fields:get")
async def get_user_field(
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/user_fields/get.html",
        {**context, **list_context, "user_field": user_field},
    )


@router.api_route(
    "/create", methods=["GET", "POST"], name="dashboard.user_fields:create"
)
async def create_user_field(
    request: Request,
    hx_trigger: str | None = Header(None),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_class = await UserFieldCreateForm.get_form_class(request)
    form_helper = FormHelper(
        form_class,
        "admin/user_fields/create.html",
        request=request,
        context={**context, **list_context},
    )
    form = await form_helper.get_form()
    if hasattr(form, "configuration"):
        configuration_form: UserFieldConfigurationBase = form.configuration
        configuration_form.set_dynamic_parameters()

    if hx_trigger is None and await form_helper.is_submitted_and_valid():

        existing_user_field = await repository.get_by_slug(form.data["slug"])
        if existing_user_field is not None:
            form.slug.errors.append("A user field with this slug already exists.")
            return await form_helper.get_error_response(
                "A user field with this slug already exists.",
                "user_field_slug_already_exists",
            )

        user_field = UserField()
        form.populate_obj(user_field)
        user_field = await repository.create(user_field)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, user_field)

        return HXRedirectResponse(
            request.url_for("dashboard.user_fields:get", id=user_field.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(user_field.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.user_fields:update",
)
async def update_user_field(
    request: Request,
    hx_trigger: str | None = Header(None),
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_class = await UserFieldUpdateForm.get_form_class(user_field)
    form_helper = FormHelper(
        form_class,
        "admin/user_fields/edit.html",
        object=user_field,
        request=request,
        context={**context, **list_context, "user_field": user_field},
    )
    form = await form_helper.get_form()
    configuration_form: UserFieldConfigurationBase = form.configuration
    configuration_form.set_dynamic_parameters()

    if hx_trigger is None and await form_helper.is_submitted_and_valid():

        existing_user_field = await repository.get_by_slug(form.data["slug"])
        if existing_user_field is not None and existing_user_field.id != user_field.id:
            form.slug.errors.append("A user field with this slug already exists.")
            return await form_helper.get_error_response(
                "A user field with this slug already exists.",
                "user_field_slug_already_exists",
            )

        form = await form_helper.get_form()
        form.populate_obj(user_field)

        await repository.update(user_field)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, user_field)

        return HXRedirectResponse(
            request.url_for("dashboard.user_fields:get", id=user_field.id)
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/delete",
    methods=["GET", "DELETE"],
    name="dashboard.user_fields:delete",
)
async def delete_user_field(
    request: Request,
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    if request.method == "DELETE":
        await repository.delete(user_field)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, user_field)

        return HXRedirectResponse(
            request.url_for("dashboard.user_fields:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            "admin/user_fields/delete.html",
            {**context, **list_context, "user_field": user_field},
        )
