import uuid

from sqlalchemy import select

from fief.models import WebhookLog
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class WebhookLogRepository(BaseRepository[WebhookLog], UUIDRepositoryMixin[WebhookLog]):
    model = WebhookLog

    async def get_by_id_and_webhook(
        self, id: uuid.UUID, webhook: uuid.UUID
    ) -> WebhookLog | None:
        statement = select(WebhookLog).where(
            WebhookLog.id == id, WebhookLog.webhook_id == webhook
        )
        return await self.get_one_or_none(statement)
