from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel

if TYPE_CHECKING:
    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property


class EmailDomainDNSRecord(BaseModel):
    id: str
    type: str
    host: str
    value: str
    verified: bool


class EmailDomain(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "email_domains"

    email_provider: Mapped[str] = mapped_column(String(length=255), nullable=False)
    domain_id: Mapped[str] = mapped_column(String(length=255), nullable=False)
    domain: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)

    _records: Mapped[list[dict[str, Any]]] = mapped_column(
        "records", JSON, nullable=False
    )

    @hybrid_property
    def records(self) -> list[EmailDomainDNSRecord]:
        return [EmailDomainDNSRecord(**record) for record in self._records]

    @records.setter
    def records(self, records: list[dict[str, Any]]):
        self._records = records

    def is_verified(self) -> bool:
        for record in self.records:
            if not record.verified:
                return False
        return True
