from fief.models import Webhook
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class WebhookRepository(BaseRepository[Webhook], UUIDRepositoryMixin[Webhook]):
    model = Webhook
