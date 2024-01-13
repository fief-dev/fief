import jinja2.exceptions
from fastapi import APIRouter, Depends, Query, Request

from fief import schemas
from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.email_template import EmailTemplateUpdateForm
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.db import AsyncSession
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.db import get_main_async_session
from fief.dependencies.email_template import (
    get_email_template_by_id_or_404,
    get_paginated_email_templates,
)
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.repositories import get_repository
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, EmailTemplate
from fief.repositories import EmailTemplateRepository
from fief.services.email_template.contexts import EMAIL_TEMPLATE_CONTEXT_CLASS_MAP
from fief.services.email_template.renderers import (
    EmailSubjectRenderer,
    EmailTemplateRenderer,
)
from fief.services.email_template.types import EmailTemplateType
from fief.services.webhooks.models import EmailTemplateUpdated
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("Type", "type", "type_column", ordering="type"),
        DatatableColumn("Subject", "subject", "subject_column"),
        DatatableColumn("Actions", "actions", "actions_column"),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["type", "subject", "actions"])
    ),
    paginated_email_templates: PaginatedObjects[EmailTemplate] = Depends(
        get_paginated_email_templates
    ),
):
    email_templates, count = paginated_email_templates
    return {
        "email_templates": email_templates,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


@router.get("/", name="dashboard.email_templates:list")
async def list_email_templates(
    request: Request,
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        request, "admin/email_templates/list.html", {**context, **list_context}
    )


@router.api_route(
    "/{id:uuid}/edit",
    methods=["GET", "POST"],
    name="dashboard.email_templates:update",
)
async def update_email_template(
    request: Request,
    preview: bool = Query(False),
    email_template: EmailTemplate = Depends(get_email_template_by_id_or_404),
    repository: EmailTemplateRepository = Depends(
        get_repository(EmailTemplateRepository)
    ),
    session: AsyncSession = Depends(get_main_async_session),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    form_helper = FormHelper(
        EmailTemplateUpdateForm,
        "admin/email_templates/edit.html",
        object=email_template,
        request=request,
        context={**context, "email_template": email_template},
    )

    context_class = EMAIL_TEMPLATE_CONTEXT_CLASS_MAP[email_template.type]
    sample_context = await context_class.create_sample_context(session)

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        email_template_preview = EmailTemplate(
            type=email_template.type,
            subject=form.data["subject"],
            content=form.data["content"],
        )
        email_subject_renderer = EmailSubjectRenderer(
            repository,
            templates_overrides={email_template.type: email_template_preview},
        )
        email_template_renderer = EmailTemplateRenderer(
            repository,
            templates_overrides={email_template.type: email_template_preview},
        )
        try:
            subject = await email_subject_renderer.render(
                EmailTemplateType[email_template_preview.type],
                sample_context,
            )  # type: ignore
            content = await email_template_renderer.render(
                EmailTemplateType[email_template_preview.type],
                sample_context,
            )  # type: ignore
        except jinja2.exceptions.TemplateError as e:
            return await form_helper.get_error_response(
                f"The template is invalid: {e!r}", "invalid_template"
            )

        if not preview:
            form.populate_obj(email_template)
            await repository.update(email_template)
            audit_logger.log_object_write(
                AuditLogMessage.OBJECT_UPDATED, email_template
            )
            trigger_webhooks(
                EmailTemplateUpdated,
                email_template,
                schemas.email_template.EmailTemplate,
            )
            return HXRedirectResponse(request.url_for("dashboard.email_templates:list"))

    else:
        email_subject_renderer = EmailSubjectRenderer(repository)
        email_template_renderer = EmailTemplateRenderer(repository)
        subject = await email_subject_renderer.render(
            EmailTemplateType[email_template.type], sample_context
        )  # type: ignore
        content = await email_template_renderer.render(
            EmailTemplateType[email_template.type], sample_context
        )  # type: ignore

    form_helper.context["subject_preview"] = subject
    form_helper.context["content_preview"] = content

    return await form_helper.get_response()
