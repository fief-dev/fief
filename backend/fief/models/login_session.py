import secrets
from typing import cast

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.settings import settings


class LoginSession(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "login_sessions"
    __lifetime_seconds__ = settings.login_session_lifetime_seconds

    token: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    response_type: str = Column(String(length=255), nullable=False)
    response_mode: str = Column(String(length=255), nullable=False)
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: list[str] = Column(JSON, nullable=False, default=list)
    prompt: str | None = Column(String(length=255), nullable=True)
    state: str | None = Column(String(length=2048), nullable=True)
    nonce: str | None = Column(String(length=255), nullable=True)
    code_challenge: str | None = Column(String(length=255), nullable=True)
    code_challenge_method: str | None = Column(String(length=255), nullable=True)

    client_id: UUID4 = Column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Client = relationship("Client", lazy="joined")

    def get_code_challenge_tuple(self) -> tuple[str, str] | None:
        if self.code_challenge is not None:
            return (self.code_challenge, cast(str, self.code_challenge_method))
        return None
