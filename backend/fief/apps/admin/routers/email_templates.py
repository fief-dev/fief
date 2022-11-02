from fastapi import APIRouter, Depends

from fief import schemas
from fief.db import AsyncSession
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.dependencies.email_template import (
    get_email_subject_renderer,
    get_email_template_by_id_or_404,
    get_email_template_renderer,
    get_paginated_email_templates,
)
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, EmailTemplate
from fief.repositories.email_template import EmailTemplateRepository
from fief.schemas.generics import PaginatedResults
from fief.services.email_template.contexts import EMAIL_TEMPLATE_CONTEXT_CLASS_MAP
from fief.services.email_template.renderers import (
    EmailSubjectRenderer,
    EmailTemplateRenderer,
)
from fief.services.email_template.types import EmailTemplateType

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


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


@router.get(
    "/{id:uuid}/preview",
    name="email_templates:preview",
    response_model=schemas.email_template.EmailTemplatePreview,
)
async def preview_email_template(
    email_template: EmailTemplate = Depends(get_email_template_by_id_or_404),
    session: AsyncSession = Depends(get_current_workspace_session),
    email_template_renderer: EmailTemplateRenderer = Depends(
        get_email_template_renderer
    ),
    email_subject_renderer: EmailSubjectRenderer = Depends(get_email_subject_renderer),
) -> schemas.email_template.EmailTemplatePreview:
    context_class = EMAIL_TEMPLATE_CONTEXT_CLASS_MAP[email_template.type]
    sample_context = await context_class.create_sample_context(session)
    subject = await email_subject_renderer.render(EmailTemplateType[email_template.type], sample_context)  # type: ignore
    content = await email_template_renderer.render(EmailTemplateType[email_template.type], sample_context)  # type: ignore
    return schemas.email_template.EmailTemplatePreview(subject=subject, content=content)


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
) -> schemas.email_template.EmailTemplate:
    email_template_update_dict = email_template_update.dict(exclude_unset=True)

    for field, value in email_template_update_dict.items():
        setattr(email_template, field, value)

    await repository.update(email_template)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, email_template)

    return schemas.email_template.EmailTemplate.from_orm(email_template)
