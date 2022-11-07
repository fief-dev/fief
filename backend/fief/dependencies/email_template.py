from typing import Dict, List, Tuple

from fastapi import Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from fief import schemas
from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import EmailTemplate
from fief.repositories import EmailTemplateRepository
from fief.services.email_template.renderers import (
    EmailSubjectRenderer,
    EmailTemplateRenderer,
)
from fief.services.email_template.types import EmailTemplateType


async def get_paginated_email_templates(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: EmailTemplateRepository = Depends(
        get_workspace_repository(EmailTemplateRepository)
    ),
) -> Tuple[List[EmailTemplate], int]:
    statement = select(EmailTemplate)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_email_template_by_id_or_404(
    id: UUID4,
    repository: EmailTemplateRepository = Depends(
        get_workspace_repository(EmailTemplateRepository)
    ),
) -> EmailTemplate:
    email_template = await repository.get_by_id(id)

    if email_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return email_template


async def get_preview_templates_overrides(
    email_template_preview_input: schemas.email_template.EmailTemplatePreviewInput,
) -> Dict[EmailTemplateType, EmailTemplate]:
    email_template = EmailTemplate(**email_template_preview_input.dict())
    return {email_template.type: email_template}


async def get_email_template_renderer(
    preview_templates_overrides: Dict[EmailTemplateType, EmailTemplate] = Depends(
        get_preview_templates_overrides
    ),
    repository: EmailTemplateRepository = Depends(
        get_workspace_repository(EmailTemplateRepository)
    ),
) -> EmailTemplateRenderer:
    return EmailTemplateRenderer(
        repository, templates_overrides=preview_templates_overrides
    )


async def get_email_subject_renderer(
    preview_templates_overrides: Dict[EmailTemplateType, EmailTemplate] = Depends(
        get_preview_templates_overrides
    ),
    repository: EmailTemplateRepository = Depends(
        get_workspace_repository(EmailTemplateRepository)
    ),
) -> EmailSubjectRenderer:
    return EmailSubjectRenderer(
        repository, templates_overrides=preview_templates_overrides
    )
