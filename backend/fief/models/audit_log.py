from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import UUID4
from sqlalchemy import JSON, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, TIMESTAMPAware, UUIDModel
from fief.models.user import User


class AuditLogMessage(str, Enum):
    USER_REGISTERED = "USER_REGISTERED"
    USER_UPDATED = "USER_UPDATED"
    USER_FORGOT_PASSWORD_REQUESTED = "USER_FORGOT_PASSWORD_REQUESTED"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    USER_TOKEN_GENERATED = "USER_TOKEN_GENERATED"


class AuditLog(UUIDModel, WorkspaceBase):
    __tablename__ = "audit_logs"

    timestamp: datetime = Column(
        TIMESTAMPAware(timezone=True), nullable=False, index=True
    )
    level: str = Column(String(length=255), nullable=False, index=True)
    message: str = Column(Text, nullable=False, index=True)
    extra: Dict = Column(JSON, nullable=True)
    author_user_id: Optional[UUID4] = Column(
        GUID, ForeignKey(User.id, ondelete="SET NULL"), nullable=True
    )
    subject_user_id: Optional[UUID4] = Column(
        GUID, ForeignKey(User.id, ondelete="SET NULL"), nullable=True
    )

    author_user: Optional[User] = relationship(
        "User", foreign_keys="AuditLog.author_user_id"
    )
    subject_user: Optional[User] = relationship(
        "User", foreign_keys="AuditLog.subject_user_id"
    )

    def __repr__(self) -> str:
        return f"AuditLog(id={self.id}, timestamp={self.timestamp}, message={self.message}, author_user_id={self.author_user_id}, subject_user_id={self.subject_user_id})"
