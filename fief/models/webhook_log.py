from pydantic import UUID4
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.webhook import Webhook


class WebhookLog(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "webhook_logs"

    webhook_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Webhook.id, ondelete="CASCADE"), nullable=False
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
