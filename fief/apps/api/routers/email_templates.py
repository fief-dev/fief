from fastapi import APIRouter, Depends

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin_api
from fief.dependencies.email_template import (
    get_email_template_by_id_or_404,
    get_paginated_email_templates,
)
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, EmailTemplate
from fief.repositories.email_template import EmailTemplateRepository
from fief.schemas.generics import PaginatedResults
from fief.services.webhooks.models import EmailTemplateUpdated

router = APIRouter(dependencies=[Depends(is_authenticated_admin_api)])


@router.get(
    "/",
    name="email_templates:list",
    response_model=PaginatedResults[schemas.email_template.EmailTemplate],
)
async def list_email_templates(
    paginated_email_templates: PaginatedObjects[EmailTemplate] = Depends(
        get_paginated_email_templates
    ),
) -> PaginatedResults[schemas.email_template.EmailTemplate]:
    email_templates, count = paginated_email_templates
    return PaginatedResults(
        count=count,
        results=[
            schemas.email_template.EmailTemplate.from_orm(email_template)
            for email_template in email_templates
        ],
    )


@router.get(
    "/{id:uuid}",
    name="email_templates:get",
    response_model=schemas.email_template.EmailTemplate,
)
async def get_email_template(
    email_template: EmailTemplate = Depends(get_email_template_by_id_or_404),
) -> schemas.email_template.EmailTemplate:
    return schemas.email_template.EmailTemplate.from_orm(email_template)


@router.patch(
    "/{id:uuid}",
    name="email_templates:update",
    response_model=schemas.email_template.EmailTemplate,
)
async def update_email_template(
    email_template_update: schemas.email_template.EmailTemplateUpdate,
    email_template: EmailTemplate = Depends(get_email_template_by_id_or_404),
    repository: EmailTemplateRepository = Depends(
        get_workspace_repository(EmailTemplateRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.email_template.EmailTemplate:
    email_template_update_dict = email_template_update.dict(exclude_unset=True)

    for field, value in email_template_update_dict.items():
        setattr(email_template, field, value)

    await repository.update(email_template)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, email_template)
    trigger_webhooks(
        EmailTemplateUpdated,
        email_template,
        schemas.email_template.EmailTemplate,
    )

    return schemas.email_template.EmailTemplate.from_orm(email_template)
