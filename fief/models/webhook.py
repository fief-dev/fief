import secrets

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, PydanticUrlString, UUIDModel


class Webhook(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "webhooks"

    url: Mapped[str] = mapped_column(
        PydanticUrlString(String)(length=255), nullable=False
    )
    secret: Mapped[str] = mapped_column(
        String(length=255), default=secrets.token_urlsafe, nullable=False
    )
    events: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    def regenerate_secret(self) -> str:
        self.secret = secrets.token_urlsafe()
        return self.secret
