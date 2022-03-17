from typing import TYPE_CHECKING, List, Optional, Union

from sqlalchemy import Column, Enum, String, Text, engine, event
from sqlalchemy.orm import relationship

from fief.crypto.encryption import decrypt, encrypt
from fief.db.types import DatabaseType, create_database_url
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
    database_host: Optional[str] = Column(Text, nullable=True)
    database_port: Optional[str] = Column(Text, nullable=True)
    database_username: Optional[str] = Column(Text, nullable=True)
    database_password: Optional[str] = Column(Text, nullable=True)
    database_name: Optional[str] = Column(Text, nullable=True)

    workspace_users: List["WorkspaceUser"] = relationship(
        "WorkspaceUser", back_populates="workspace", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"Workspace(id={self.id}, name={self.name}, domain={self.domain})"

    def get_database_url(self, asyncio=True) -> engine.URL:
        """
        Return the database URL for this workspace.

        If it's not specified on the model, the instance database URL is returned.
        """
        if self.database_type is None:
            url = settings.get_database_url(asyncio, schema=self.get_schema_name())
        else:
            url = create_database_url(
                self.database_type,
                asyncio=asyncio,
                username=self._decrypt_database_setting("database_username"),
                password=self._decrypt_database_setting("database_password"),
                host=self._decrypt_database_setting("database_host"),
                port=self._decrypt_database_port(),
                database=self._decrypt_database_setting("database_name"),
                path=settings.database_location,
                schema=self.get_schema_name(),
            )

        return url

    def get_schema_name(self) -> str:
        """
        Return the SQL schema name where the data is stored.
        """
        return str(self.id)

    def _decrypt_database_setting(self, attribute: str) -> Optional[str]:
        value = getattr(self, attribute)
        if value is None:
            return value
        return decrypt(value, settings.encryption_key)

    def _decrypt_database_port(self) -> Optional[int]:
        value = self._decrypt_database_setting("database_port")
        if value is None:
            return value
        return int(value)


def encrypt_database_setting(
    target: Workspace,
    value: Optional[Union[str, int]],
    oldvalue: Optional[str],
    initiator,
):
    if value is None:
        return value
    return encrypt(str(value), settings.encryption_key)


event.listen(Workspace.database_host, "set", encrypt_database_setting, retval=True)
event.listen(Workspace.database_port, "set", encrypt_database_setting, retval=True)
event.listen(Workspace.database_username, "set", encrypt_database_setting, retval=True)
event.listen(Workspace.database_password, "set", encrypt_database_setting, retval=True)
event.listen(Workspace.database_name, "set", encrypt_database_setting, retval=True)
