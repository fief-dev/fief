from typing import Any

from pydantic import BaseModel


class WebhookEventType:
    """Base webhook event type."""

    object: str
    event: str

    def __new__(cls):
        raise TypeError("WebhookEventType can't be instantiated.")  # noqa: TC003

    @classmethod
    def key(cls) -> str:
        return f"{cls.object}.{cls.event}"

    @classmethod
    def description(cls) -> str | None:
        return cls.__doc__


class ClientCreated(WebhookEventType):
    """Occurs whenever a Client is created."""

    object = "client"
    event = "created"


class ClientUpdated(WebhookEventType):
    """Occurs whenever a Client is updated."""

    object = "client"
    event = "updated"


class EmailTemplateUpdated(WebhookEventType):
    """Occurs whenever an Email Template is updated."""

    object = "email_template"
    event = "updated"


class OAuthProviderCreated(WebhookEventType):
    """Occurs whenever an OAuth Provider is created."""

    object = "oauth_provider"
    event = "created"


class OAuthProviderUpdated(WebhookEventType):
    """Occurs whenever an OAuth Provider is updated."""

    object = "oauth_provider"
    event = "updated"


class OAuthProviderDeleted(WebhookEventType):
    """Occurs whenever an OAuth Provider is deleted."""

    object = "oauth_provider"
    event = "deleted"


class PermissionCreated(WebhookEventType):
    """Occurs whenever a Permission is created."""

    object = "permission"
    event = "created"


class PermissionUpdated(WebhookEventType):
    """Occurs whenever a Permission is updated."""

    object = "permission"
    event = "updated"


class PermissionDeleted(WebhookEventType):
    """Occurs whenever a Permission is deleted."""

    object = "permission"
    event = "deleted"


class RoleCreated(WebhookEventType):
    """Occurs whenever a Role is created."""

    object = "role"
    event = "created"


class RoleUpdated(WebhookEventType):
    """Occurs whenever a Role is updated."""

    object = "role"
    event = "updated"


class RoleDeleted(WebhookEventType):
    """Occurs whenever a Role is deleted."""

    object = "role"
    event = "deleted"


class TenantCreated(WebhookEventType):
    """Occurs whenever a Tenant is created."""

    object = "tenant"
    event = "created"


class TenantUpdated(WebhookEventType):
    """Occurs whenever a Tenant is updated."""

    object = "tenant"
    event = "updated"


class UserCreated(WebhookEventType):
    """Occurs whenever a User is created."""

    object = "user"
    event = "created"


class UserUpdated(WebhookEventType):
    """Occurs whenever a User is updated."""

    object = "user"
    event = "updated"


class UserForgotPasswordRequested(WebhookEventType):
    """Occurs whenever a User requested to reset their password."""

    object = "user"
    event = "forgot_password_requested"


class UserPasswordReset(WebhookEventType):
    """Occurs whenever a User successfully reset their password."""

    object = "user"
    event = "password_reset"


class UserFieldCreated(WebhookEventType):
    """Occurs whenever a User Field is created."""

    object = "user_field"
    event = "created"


class UserFieldUpdated(WebhookEventType):
    """Occurs whenever a User Field is updated."""

    object = "user_field"
    event = "updated"


class UserFieldDeleted(WebhookEventType):
    """Occurs whenever a User Field is deleted."""

    object = "user_field"
    event = "deleted"


class UserPermissionCreated(WebhookEventType):
    """Occurs whenever a User Permission is created."""

    object = "user_permission"
    event = "created"


class UserPermissionDeleted(WebhookEventType):
    """Occurs whenever a User Permission is deleted."""

    object = "user_permission"
    event = "deleted"


class UserRoleCreated(WebhookEventType):
    """Occurs whenever a User Role is created."""

    object = "user_role"
    event = "created"


class UserRoleDeleted(WebhookEventType):
    """Occurs whenever a User Role is deleted."""

    object = "user_role"
    event = "deleted"


WEBHOOK_EVENTS: list[type[WebhookEventType]] = [
    ClientCreated,
    ClientUpdated,
    EmailTemplateUpdated,
    OAuthProviderCreated,
    OAuthProviderUpdated,
    OAuthProviderDeleted,
    PermissionCreated,
    PermissionUpdated,
    PermissionDeleted,
    RoleCreated,
    RoleUpdated,
    RoleDeleted,
    TenantCreated,
    TenantUpdated,
    UserCreated,
    UserUpdated,
    UserForgotPasswordRequested,
    UserPasswordReset,
    UserFieldCreated,
    UserFieldUpdated,
    UserFieldDeleted,
    UserPermissionCreated,
    UserPermissionDeleted,
    UserRoleCreated,
    UserRoleDeleted,
]


class WebhookEvent(BaseModel):
    type: str
    data: dict[str, Any]
