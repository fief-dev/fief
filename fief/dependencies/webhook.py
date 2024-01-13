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
from fief.models import Webhook, WebhookLog
from fief.repositories import WebhookLogRepository, WebhookRepository


async def get_paginated_webhooks(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: WebhookRepository = Depends(WebhookRepository),
    get_paginated_objects: GetPaginatedObjects[Webhook] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[Webhook]:
    statement = select(Webhook)

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_webhook_by_id_or_404(
    id: UUID4,
    repository: WebhookRepository = Depends(WebhookRepository),
) -> Webhook:
    webhook = await repository.get_by_id(id)

    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return webhook


async def get_paginated_webhook_logs(
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter([(["created_at"], True)])),
    repository: WebhookLogRepository = Depends(WebhookLogRepository),
    get_paginated_objects: GetPaginatedObjects[WebhookLog] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[WebhookLog]:
    statement = select(WebhookLog).where(WebhookLog.webhook_id == webhook.id)

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_webhook_log_by_id_and_webhook_or_404(
    log_id: UUID4,
    webhook: Webhook = Depends(get_webhook_by_id_or_404),
    repository: WebhookLogRepository = Depends(WebhookLogRepository),
) -> WebhookLog:
    webhook_log = await repository.get_by_id_and_webhook(log_id, webhook.id)

    if webhook_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return webhook_log
