from typing import Optional

from sqlalchemy import Column, Enum, Integer, String, engine

from fief.db.types import DatabaseType, get_driver
from fief.models.base import GlobalBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.settings import settings


class Account(UUIDModel, CreatedUpdatedAt, GlobalBase):
    __tablename__ = "accounts"

    name: str = Column(String(length=255), nullable=False)
    domain: str = Column(String(length=255), nullable=False)

    database_type: Optional[DatabaseType] = Column(Enum(DatabaseType), nullable=True)
    database_host: Optional[str] = Column(String(length=2048), nullable=True)
    database_port: Optional[int] = Column(Integer, nullable=True)
    database_username: Optional[str] = Column(String(length=2048), nullable=True)
    database_password: Optional[str] = Column(String(length=2048), nullable=True)
    database_name: Optional[str] = Column(String(length=2048), nullable=True)

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name={self.name}, domain={self.domain})"

    def get_database_url(self, asyncio=True) -> engine.URL:
        """
        Return the database URL for this account.

        If it's not specified on the model, the instance database URL is returned.
        """
        if self.database_type is None:
            return settings.get_database_url(asyncio)

        return engine.URL.create(
            drivername=get_driver(self.database_type, asyncio=asyncio),
            username=self.database_username,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )

    def get_schema_name(self) -> str:
        """
        Return the SQL schema name where the data is stored.
        """
        return str(self.id)
