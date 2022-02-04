from typing import Optional, Union, cast

from sqlalchemy import Column, Enum, String, Text, engine, event

from fief.crypto.encryption import decrypt, encrypt
from fief.db.types import DatabaseType, get_driver
from fief.models.base import GlobalBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.settings import settings


class Account(UUIDModel, CreatedUpdatedAt, GlobalBase):
    __tablename__ = "accounts"

    name: str = Column(String(length=255), nullable=False)
    domain: str = Column(String(length=255), nullable=False)

    database_type: Optional[DatabaseType] = Column(Enum(DatabaseType), nullable=True)
    database_host: Optional[str] = Column(Text, nullable=True)
    database_port: Optional[str] = Column(Text, nullable=True)
    database_username: Optional[str] = Column(Text, nullable=True)
    database_password: Optional[str] = Column(Text, nullable=True)
    database_name: Optional[str] = Column(Text, nullable=True)

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
            username=decrypt(
                cast(str, self.database_username), settings.encryption_key
            ),
            password=decrypt(
                cast(str, self.database_password), settings.encryption_key
            ),
            host=decrypt(cast(str, self.database_host), settings.encryption_key),
            port=int(decrypt(cast(str, self.database_port), settings.encryption_key)),
            database=decrypt(cast(str, self.database_name), settings.encryption_key),
        )

    def get_schema_name(self) -> str:
        """
        Return the SQL schema name where the data is stored.
        """
        return str(self.id)


def encrypt_database_setting(
    target: Account,
    value: Optional[Union[str, int]],
    oldvalue: Optional[str],
    initiator,
):
    if value is None:
        return value
    return encrypt(str(value), settings.encryption_key)


event.listen(Account.database_host, "set", encrypt_database_setting, retval=True)
event.listen(Account.database_port, "set", encrypt_database_setting, retval=True)
event.listen(Account.database_username, "set", encrypt_database_setting, retval=True)
event.listen(Account.database_password, "set", encrypt_database_setting, retval=True)
event.listen(Account.database_name, "set", encrypt_database_setting, retval=True)
