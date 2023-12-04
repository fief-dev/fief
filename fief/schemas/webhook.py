from enum import StrEnum

from pydantic import BaseModel, HttpUrl

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.services.webhooks.models import WEBHOOK_EVENTS

WebhookEventType = StrEnum(  # type: ignore
    "WebhookEventType",
    [event.key() for event in WEBHOOK_EVENTS],
)


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[WebhookEventType]


class WebhookUpdate(BaseModel):
    url: HttpUrl | None = None
    events: list[WebhookEventType] | None = None


class BaseWebhook(UUIDSchema, CreatedUpdatedAt):
    url: HttpUrl
    events: list[WebhookEventType]


class Webhook(BaseWebhook):
    pass


class WebhookSecret(BaseWebhook):
    secret: str
