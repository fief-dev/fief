from typing import Optional

from sqlalchemy import Column, String, Text

from fief.models.base import GlobalBase
from fief.models.generics import UUIDModel
from fief.settings import settings
from fief.utils.db_connection import get_database_url


class Account(UUIDModel, GlobalBase):
    __tablename__ = "accounts"

    name: str = Column(String(length=255), nullable=False)
    domain: str = Column(String(length=255), nullable=False)
    database_url: Optional[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name={self.name}, domain={self.domain})"

    def get_database_url(self, asyncio=True) -> str:
        """
        Return the database URL for this account.

        If it's not specified on the model, the instance database URL is returned.
        """
        if self.database_url is None:
            return settings.get_database_url()

        return get_database_url(self.database_url, asyncio)
