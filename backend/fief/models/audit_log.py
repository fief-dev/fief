from datetime import datetime
from enum import Enum

from pydantic import UUID4
from sqlalchemy import JSON, Column, String, Text
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, TIMESTAMPAware, UUIDModel
from fief.models.user import User


class AuditLogMessage(str, Enum):
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

    timestamp: datetime = Column(
        TIMESTAMPAware(timezone=True), nullable=False, index=True
    )
    level: str = Column(String(length=255), nullable=False, index=True)
    message: str = Column(Text, nullable=False)
    extra: dict = Column(JSON, nullable=True)

    subject_user_id: UUID4 | None = Column(GUID, nullable=True, index=True)

    object_id: UUID4 | None = Column(GUID, nullable=True, index=True)
    object_class: str | None = Column(String(length=255), nullable=True, index=True)

    admin_user_id: UUID4 | None = Column(GUID, nullable=True, index=True)
    admin_api_key_id: UUID4 | None = Column(GUID, nullable=True, index=True)

    subject_user: User | None = relationship(
        "User",
        # Define a relationship, but without a foreign key constraint
        foreign_keys="AuditLog.subject_user_id",
        primaryjoin="AuditLog.subject_user_id == User.id",
    )
