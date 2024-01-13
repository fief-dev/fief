from fastapi import Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.repositories import get_repository
from fief.models import EmailTemplate
from fief.repositories import EmailTemplateRepository


async def get_paginated_email_templates(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: EmailTemplateRepository = Depends(
        get_repository(EmailTemplateRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[EmailTemplate] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[EmailTemplate]:
    statement = select(EmailTemplate)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_email_template_by_id_or_404(
    id: UUID4,
    repository: EmailTemplateRepository = Depends(
        get_repository(EmailTemplateRepository)
    ),
) -> EmailTemplate:
    email_template = await repository.get_by_id(id)

    if email_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return email_template
