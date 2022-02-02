import functools
import json
import secrets
from typing import Any, Dict

from fief_client import FiefTokenResponse
from sqlalchemy import Column, String, Text

from fief.models.base import GlobalBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class AdminSessionToken(UUIDModel, CreatedUpdatedAt, GlobalBase):
    __tablename__ = "admin_session_tokens"

    token: str = Column(
        String(length=255), default=secrets.token_urlsafe, unique=True, nullable=False
    )
    raw_tokens: str = Column(Text, nullable=False)
    raw_userinfo: str = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"AdminSessionToken(id={self.id})"

    @functools.cached_property
    def tokens(self) -> FiefTokenResponse:
        return json.loads(self.raw_tokens)

    @functools.cached_property
    def userinfo(self) -> Dict[str, Any]:
        return json.loads(self.raw_userinfo)
