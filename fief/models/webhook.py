import secrets

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Webhook(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "webhooks"

    url: Mapped[str] = mapped_column(String(length=255), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(length=255), default=secrets.token_urlsafe, nullable=False
    )
