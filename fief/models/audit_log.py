from datetime import datetime
from enum import StrEnum

from pydantic import UUID4
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, TIMESTAMPAware, UUIDModel
from fief.models.user import User


class AuditLogMessage(StrEnum):
    OBJECT_CREATED = "OBJECT_CREATED"
    OBJECT_UPDATED = "OBJECT_UPDATED"
    OBJECT_DELETED = "OBJECT_DELETED"
    USER_REGISTERED = "USER_REGISTERED"
    USER_UPDATED = "USER_UPDATED"
    USER_FORGOT_PASSWORD_REQUESTED = "USER_FORGOT_PASSWORD_REQUESTED"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    USER_TOKEN_GENERATED = "USER_TOKEN_GENERATED"
    USER_TOKEN_GENERATED_BY_ADMIN = "USER_TOKEN_GENERATED_BY_ADMIN"
    OAUTH_PROVIDER_USER_ACCESS_TOKEN_GET = "OAUTH_PROVIDER_USER_ACCESS_TOKEN_GET"


class AuditLog(UUIDModel, WorkspaceBase):
    __tablename__ = "audit_logs"

    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMPAware(timezone=True), nullable=False, index=True
    )
    level: Mapped[str] = mapped_column(String(length=255), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    extra: Mapped[dict] = mapped_column(JSON, nullable=True)

    subject_user_id: Mapped[UUID4 | None] = mapped_column(
        GUID, nullable=True, index=True
    )

    object_id: Mapped[UUID4 | None] = mapped_column(GUID, nullable=True, index=True)
    object_class: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True, index=True
    )

    admin_user_id: Mapped[UUID4 | None] = mapped_column(GUID, nullable=True, index=True)
    admin_api_key_id: Mapped[UUID4 | None] = mapped_column(
        GUID, nullable=True, index=True
    )

    subject_user: Mapped[User | None] = relationship(
        "User",
        # Define a relationship, but without a foreign key constraint
        foreign_keys="AuditLog.subject_user_id",
        primaryjoin="AuditLog.subject_user_id == User.id",
    )
