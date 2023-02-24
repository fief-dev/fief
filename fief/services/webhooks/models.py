from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class WebhookEventType(StrEnum):
    OBJECT_CREATED = "OBJECT_CREATED"
    OBJECT_UPDATED = "OBJECT_UPDATED"
    OBJECT_DELETED = "OBJECT_DELETED"
    USER_REGISTERED = "USER_REGISTERED"
    USER_UPDATED = "USER_UPDATED"
    USER_FORGOT_PASSWORD_REQUESTED = "USER_FORGOT_PASSWORD_REQUESTED"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"


class WebhookEvent(BaseModel):
    type: WebhookEventType
    object: str
    data: dict[str, Any]
