from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Enum, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType

from fief.crypto.encryption import FernetEngine
from fief.db.types import (
    DatabaseConnectionParameters,
    DatabaseType,
    create_database_connection_parameters,
)
from fief.models.base import MainBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.settings import settings

if TYPE_CHECKING:
    from fief.models.workspace_user import WorkspaceUser


class Workspace(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "workspaces"

    name: str = Column(String(length=255), nullable=False)
    domain: str = Column(String(length=255), nullable=False)

    database_type: Optional[DatabaseType] = Column(Enum(DatabaseType), nullable=True)
    database_host: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    database_port: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    database_username: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    database_password: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    database_name: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    database_ssl_mode: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )

    alembic_revision: Optional[str] = Column(
        String(length=255), nullable=True, index=True
    )

    workspace_users: List["WorkspaceUser"] = relationship(
        "WorkspaceUser", back_populates="workspace", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"Workspace(id={self.id}, name={self.name}, domain={self.domain})"

    def get_database_connection_parameters(
        self, asyncio=True
    ) -> DatabaseConnectionParameters:
        """
        Return the database URL and connection arguments for this workspace.

        If it's not specified on the model, the instance database URL is returned.
        """
        if self.database_type is None:
            url = settings.get_database_connection_parameters(
                asyncio, schema=self.get_schema_name()
            )
        else:
            url = create_database_connection_parameters(
                self.database_type,
                asyncio=asyncio,
                username=self.database_username,
                password=self.database_password,
                host=self.database_host,
                port=int(self.database_port) if self.database_port else None,
                database=self.database_name,
                path=settings.database_location,
                schema=self.get_schema_name(),
                ssl_mode=self.database_ssl_mode,
            )

        return url

    def get_schema_name(self) -> str:
        """
        Return the SQL schema name where the data is stored.
        """
        return str(self.id)
