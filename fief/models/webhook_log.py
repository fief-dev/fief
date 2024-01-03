import json
from typing import Any

from pydantic import UUID4
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import Base
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.webhook import Webhook


class WebhookLog(UUIDModel, CreatedUpdatedAt, Base):
    __tablename__ = "webhook_logs"

    webhook_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Webhook.id, ondelete="CASCADE"), nullable=False
    )
    event: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    webhook: Mapped[Webhook] = relationship("Webhook")

    @property
    def payload_dict(self) -> dict[str, Any]:
        return json.loads(self.payload)
