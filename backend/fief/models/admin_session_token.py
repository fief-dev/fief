import functools
import json
import uuid

from fief_client import FiefTokenResponse, FiefUserInfo
from pydantic import UUID4
from sqlalchemy import Column, String, Text

from fief.models.base import MainBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class AdminSessionToken(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "admin_session_tokens"

    token: str = Column(String(length=255), unique=True, nullable=False)
    raw_tokens: str = Column(Text, nullable=False)
    raw_userinfo: str = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"AdminSessionToken(id={self.id})"

    @functools.cached_property
    def tokens(self) -> FiefTokenResponse:
        return json.loads(self.raw_tokens)

    @functools.cached_property
    def userinfo(self) -> FiefUserInfo:
        return json.loads(self.raw_userinfo)

    @functools.cached_property
    def user_id(self) -> UUID4:
        return uuid.UUID(self.userinfo["sub"])
