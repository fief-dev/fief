import secrets

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.services.webhooks.models import WebhookEventType


class Webhook(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "webhooks"

    url: Mapped[str] = mapped_column(String(length=255), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(length=255), default=secrets.token_urlsafe, nullable=False
    )
    events: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    objects: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    def get_events_display_names(self) -> list[str]:
        return [WebhookEventType[event].get_display_name() for event in self.events]

    def regenerate_secret(self) -> str:
        self.secret = secrets.token_urlsafe()
        return self.secret
