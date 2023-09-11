from pydantic import UUID4

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.webhook import WebhookEventType


class BaseWebhookLog(UUIDSchema, CreatedUpdatedAt):
    webhook_id: UUID4
    event: WebhookEventType
    attempt: int
    payload: str
    success: bool
    response: str | None = None
    error_type: str | None = None
    error_message: str | None = None


class WebhookLog(BaseWebhookLog):
    pass
