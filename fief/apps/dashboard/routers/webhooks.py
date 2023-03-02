from fastapi import APIRouter, Depends, Request, status

from fief.apps.dashboard.dependencies import (
    BaseContext,
    DatatableColumn,
    DatatableQueryParameters,
    DatatableQueryParametersGetter,
    get_base_context,
)
from fief.apps.dashboard.forms.webhook import WebhookCreateForm, WebhookUpdateForm
from fief.apps.dashboard.responses import HXRedirectResponse
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.webhook import (
    get_paginated_webhook_logs,
    get_paginated_webhooks,
    get_webhook_by_id_or_404,
    get_webhook_log_by_id_and_webhook_or_404,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.forms import FormHelper
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Webhook, WebhookLog
from fief.repositories import WebhookRepository
from fief.templates import templates

router = APIRouter(dependencies=[Depends(is_authenticated_admin_session)])


async def get_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn("URL", "url", "url_column", ordering="url"),
        DatatableColumn(
            "Created at", "created_at", "created_at_column", ordering="created_at"
        ),
        DatatableColumn("Events", "events", "events_column"),
        DatatableColumn("Actions", "actions", "actions_column"),
    ]


async def get_list_context(
    columns: list[DatatableColumn] = Depends(get_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(["url", "created_at", "events", "actions"])
    ),
    paginated_webhooks: PaginatedObjects[Webhook] = Depends(get_paginated_webhooks),
):
    webhooks, count = paginated_webhooks
    return {
        "webhooks": webhooks,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


@router.get("/", name="dashboard.webhooks:list")
async def list_webhooks(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/webhooks/list.html", {**context, **list_context}
    )


@router.get("/{id:uuid}", name="dashboard.webhooks:get")
async def get_webhook(
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/webhooks/get.html",
        {**context, **list_context, "webhook": webhook},
    )


@router.api_route("/create", methods=["GET", "POST"], name="dashboard.webhooks:create")
async def create_webhook(
    request: Request,
    repository: WebhookRepository = Depends(
        get_workspace_repository(WebhookRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        WebhookCreateForm,
        "admin/webhooks/create.html",
        request=request,
        context={**context, **list_context},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()

        webhook = Webhook()
        form.populate_obj(webhook)

        webhook = await repository.create(webhook)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, webhook)

        return templates.TemplateResponse(
            "admin/webhooks/secret.html",
            {**context, **list_context, "webhook": webhook, "secret": webhook.secret},
            status_code=status.HTTP_201_CREATED,
            headers={"X-Fief-Object-Id": str(webhook.id)},
        )

    return await form_helper.get_response()


@router.api_route(
    "/{id:uuid}/edit", methods=["GET", "POST"], name="dashboard.webhooks:update"
)
async def update_webhook(
    request: Request,
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    repository: WebhookRepository = Depends(
        get_workspace_repository(WebhookRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    form_helper = FormHelper(
        WebhookUpdateForm,
        "admin/webhooks/edit.html",
        object=webhook,
        request=request,
        context={**context, **list_context, "webhook": webhook},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        form.populate_obj(webhook)

        await repository.update(webhook)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, webhook)

        return HXRedirectResponse(
            request.url_for("dashboard.webhooks:get", id=webhook.id)
        )

    return await form_helper.get_response()


@router.post("/{id:uuid}/secret", name="dashboard.webhooks:secret")
async def regenerate_webhook_secret(
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    repository: WebhookRepository = Depends(
        get_workspace_repository(WebhookRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    secret = webhook.regenerate_secret()
    await repository.update(webhook)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, webhook)

    return templates.TemplateResponse(
        "admin/webhooks/secret.html",
        {**context, **list_context, "webhook": webhook, "secret": secret},
        headers={"X-Fief-Object-Id": str(webhook.id)},
    )


@router.api_route(
    "/{id:uuid}/delete", methods=["GET", "DELETE"], name="dashboard.webhooks:delete"
)
async def delete_webhook(
    request: Request,
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    repository: WebhookRepository = Depends(
        get_workspace_repository(WebhookRepository)
    ),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    if request.method == "DELETE":
        await repository.delete(webhook)
        audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, webhook)

        return HXRedirectResponse(
            request.url_for("dashboard.webhooks:list"),
            status_code=status.HTTP_204_NO_CONTENT,
        )
    else:
        return templates.TemplateResponse(
            "admin/webhooks/delete.html",
            {**context, **list_context, "webhook": webhook},
        )


async def get_logs_columns() -> list[DatatableColumn]:
    return [
        DatatableColumn(
            "Delivered at", "delivered_at", "created_at_column", ordering="created_at"
        ),
        DatatableColumn("Event", "event", "event_column", ordering="event"),
        DatatableColumn("Success", "success", "success_column", ordering="success"),
        DatatableColumn("Attempt", "attempt", "attempt_column", ordering="attempt"),
        DatatableColumn("Error", "error", "error_column", ordering="error_type"),
        DatatableColumn("Actions", "actions", "actions_column"),
    ]


async def get_logs_list_context(
    columns: list[DatatableColumn] = Depends(get_logs_columns),
    datatable_query_parameters: DatatableQueryParameters = Depends(
        DatatableQueryParametersGetter(
            ["delivered_at", "event", "success", "attempt", "error", "actions"]
        )
    ),
    paginated_webhook_logs: PaginatedObjects[WebhookLog] = Depends(
        get_paginated_webhook_logs
    ),
):
    webhook_logs, count = paginated_webhook_logs
    return {
        "webhook_logs": webhook_logs,
        "count": count,
        "datatable_query_parameters": datatable_query_parameters,
        "columns": columns,
    }


@router.get("/{id:uuid}/logs", name="dashboard.webhooks:logs")
async def list_webhook_logs(
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    list_context=Depends(get_logs_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/webhooks/logs/list.html",
        {**context, **list_context, "webhook": webhook},
    )


@router.get("/{id:uuid}/logs/{log_id:uuid}", name="dashboard.webhooks:log")
async def get_webhook_log(
    webhook_log: WebhookLog = Depends(get_webhook_log_by_id_and_webhook_or_404),
    list_context=Depends(get_logs_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "admin/webhooks/logs/get.html",
        {**context, **list_context, "webhook_log": webhook_log},
    )
