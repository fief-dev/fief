from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTable
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declared_attr

from fief.models.base import AccountBase
from fief.models.generics import GUID
from fief.models.user import User


class AccessToken(SQLAlchemyBaseAccessTokenTable, AccountBase):
    __tablename__ = "access_tokens"

    @declared_attr
    def user_id(cls) -> Column[GUID]:
        return Column(GUID, ForeignKey(User.id, ondelete="cascade"), nullable=False)
