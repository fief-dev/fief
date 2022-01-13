from jwcrypto import jwk
from sqlalchemy import Column, String, Text

from fief.auth.jwk import generate_account_signature_jwk, load_jwk
from fief.models.base import GlobalBase
from fief.models.generics import UUIDModel


class Account(UUIDModel, GlobalBase):
    __tablename__ = "accounts"

    name: str = Column(String(length=255), nullable=False)
    domain: str = Column(String(length=255), nullable=False)
    database_url: str = Column(Text, nullable=False)
    sign_jwk: str = Column(Text, nullable=False, default=generate_account_signature_jwk)

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name={self.name}, domain={self.domain})"

    def get_database_url(self, asyncio=True) -> str:
        """
        Returns a proper database URL for async or not-async context.

        Some tools like Alembic still require a sync connection.
        """
        url = self.database_url
        if asyncio:
            if url.startswith("sqlite://"):
                return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    def get_sign_jwk(self) -> jwk.JWK:
        return load_jwk(self.sign_jwk)
