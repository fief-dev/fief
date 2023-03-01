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

    def get_display_name(self) -> str:
        display_names = {
            WebhookEventType.OBJECT_CREATED: "Object Created",
            WebhookEventType.OBJECT_UPDATED: "Object Updated",
            WebhookEventType.OBJECT_DELETED: "Object Deleted",
            WebhookEventType.USER_REGISTERED: "User Registered",
            WebhookEventType.USER_UPDATED: "User Updated",
            WebhookEventType.USER_FORGOT_PASSWORD_REQUESTED: "Forgot Password Requested",
            WebhookEventType.USER_PASSWORD_RESET: "Password Reset",
        }
        return display_names[self]

    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]


OBJECT_AGNOSTIC_WEBHOOK_EVENTS: list[WebhookEventType] = [
    WebhookEventType.USER_REGISTERED,
    WebhookEventType.USER_UPDATED,
    WebhookEventType.USER_FORGOT_PASSWORD_REQUESTED,
    WebhookEventType.USER_PASSWORD_RESET,
]

WEBHOOK_OBJECTS = [
    "Client",
    "EmailTemplate",
    "OAuthProvider",
    "Permission",
    "Role",
    "Tenant",
    "User",
    "UserField",
    "UserPermission",
    "UserRole",
]


class WebhookEvent(BaseModel):
    type: WebhookEventType
    object: str
    data: dict[str, Any]
