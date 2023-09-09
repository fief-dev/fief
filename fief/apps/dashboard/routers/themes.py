from fastapi import APIRouter, Depends, Header, Query, Request, status

from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.theme import (
    ThemeCreateForm,
    ThemePagePreviewForm,
    ThemeUpdateForm,
)
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.theme import (
    get_paginated_themes,
    get_theme_by_id_or_404,
    get_theme_preview,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Theme, User
from fief.repositories import TenantRepository, ThemeRepository, UserRepository
from fief.services.theme_preview import ThemePreview
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Name", "name", "name_column", ordering="name"),
        DatatableColumn("Default", "default", "default_column"),
        DatatableColumn("Actions", "actions", "actions_column"),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["name", "default", "actions"])
    ),
    paginated_themes: PaginatedObjects[Theme] = Depends(get_paginated_themes),
):
    themes, count = paginated_themes
    return {
        "themes": themes,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/themes/list_combobox.html"
    return "admin/themes/list.html"


@router.get("/", name="dashboard.themes:list")
async def list_themes(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.themes:create")
async def create_theme(
    request: Request,
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        ThemeCreateForm,
        "admin/themes/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        theme = Theme.build_default()
        theme.default = False
        form.populate_obj(theme)

        theme = await repository.create(theme)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, theme)

        return HXRedirectResponse(
            request.url_for("dashboard.themes:update", id=theme.id),
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(theme.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.themes:update",
)
async def update_theme(
    request: Request,
    preview: str | None = Query(None),
    theme: Theme = Depends(get_theme_by_id_or_404),
    theme_preview: ThemePreview = Depends(get_theme_preview),
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
    user_repository: UserRepository = Depends(get_workspace_repository(UserRepository)),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        ThemeUpdateForm,
        "admin/themes/edit.html",
        object=theme,
        request=request,
        context={**context, **list_context, "theme": theme},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(theme)

        if preview is None:
            await repository.update(theme)
            audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, theme)
            return HXRedirectResponse(request.url_for("dashboard.themes:list"))

    preview_page = preview if preview is not None else "login"
    tenant = await tenant_repository.get_default()
    assert tenant is not None

    user = await user_repository.get_one_by_tenant(tenant.id)
    if user is None:
        user = User.create_sample(tenant)

    form_helper.context["preview_content"] = await theme_preview.preview(
        preview_page, theme, tenant=tenant, user=user, request=request
    )

    page_preview_form = ThemePagePreviewForm(data={"page": preview_page})
    form_helper.context["page_preview_form"] = page_preview_form

    return await form_helper.get_response()


@router.post(
    "/{id:uuid}/default",
    name="dashboard.themes:default",
)
async def set_default_theme(
    request: Request,
    theme: Theme = Depends(get_theme_by_id_or_404),
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    default_theme = await repository.get_default()
    if default_theme is not None and default_theme.id != theme.id:
        default_theme.default = False
        await repository.update(default_theme)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, default_theme)

        theme.default = True
        await repository.update(theme)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, theme)

    return HXRedirectResponse(request.url_for("dashboard.themes:list"))
