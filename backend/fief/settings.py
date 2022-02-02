from enum import Enum
from typing import Optional

from pydantic import BaseSettings, validator

from fief.utils.db_connection import get_database_url


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    environment: Environment
    log_level: str = "DEBUG"
    unit_tests: bool = False
    database_url: str
    root_domain: str
    allow_origin_regex: str

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

    @validator("database_url")
    def replace_postgres_scheme(cls, url: str) -> str:
        """
        Ensures scheme is compatible with newest version of SQLAlchemy.
        Ref: https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
        """
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    def get_database_url(self, asyncio=True) -> str:
        """
        Returns a proper database URL for async or not-async context.

        Some tools like Alembic still require a sync connection.
        """
        return get_database_url(self.database_url, asyncio)


settings = Settings()
