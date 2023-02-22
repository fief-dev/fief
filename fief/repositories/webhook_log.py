from fief.models import WebhookLog
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class WebhookLogRepository(BaseRepository[WebhookLog], UUIDRepositoryMixin[WebhookLog]):
    model = WebhookLog
