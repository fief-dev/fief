from enum import Enum
from typing import Optional

from pydantic import BaseSettings, validator
from sqlalchemy import engine

from fief.crypto.encryption import is_valid_key
from fief.db.types import DatabaseType, get_driver


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class InvalidEncryptionKeyError(ValueError):
    pass


class Settings(BaseSettings):
    environment: Environment
    log_level: str = "DEBUG"
    unit_tests: bool = False
    root_domain: str
    allow_origin_regex: str

    encryption_key: bytes

    database_type: DatabaseType
    database_host: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str

    account_table_prefix: str = "fief_"

    login_session_cookie_name: str = "fief_login_session"
    login_session_cookie_domain: str = ""
    login_session_cookie_secure: bool = True

    session_cookie_name: str = "fief_session"
    session_cookie_domain: str = ""
    session_cookie_secure: bool = True
    session_lifetime_seconds: int = 86400 * 30

    fief_domain: str
    fief_base_url: str
    fief_client_id: str
    fief_client_secret: str
    fief_encryption_key: Optional[str] = None

    fief_admin_session_cookie_name: str = "fief_admin_session"
    fief_admin_session_cookie_domain: str = ""
    fief_admin_session_cookie_secure: bool = True

    fief_documentation_url: str = "https://docs.fief.dev"

    class Config:
        env_file = ".env"

    @validator("encryption_key", pre=True)
    def validate_encryption_key(cls, value: Optional[str]) -> Optional[bytes]:
        if value is None:
            return value

        key = value.encode("utf-8")
        if not is_valid_key(key):
            raise InvalidEncryptionKeyError()

        return key

    def get_database_url(self, asyncio=True) -> engine.URL:
        """
        Returns a proper database URL for async or not-async context.

        Some tools like Alembic still require a sync connection.
        """
        return engine.URL.create(
            drivername=get_driver(self.database_type, asyncio=asyncio),
            username=self.database_username,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )


settings = Settings()
