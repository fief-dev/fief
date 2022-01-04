from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from fief.models.base import AccountBase
from fief.models.generics import GUID
from fief.models.tenant import Tenant


class User(SQLAlchemyBaseUserTable, AccountBase):
    __tablename__ = "users"

    tenant_id = Column(GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False)
    tenant: Tenant = relationship("Tenant", cascade="all, delete")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
