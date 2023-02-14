from typing import Any

from fastapi import Request
from jwcrypto import jwk
from pydantic import UUID4
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.routing import Router

from fief.crypto.jwk import generate_signature_jwk_string, load_jwk
from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.theme import Theme


class Tenant(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    slug: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sign_jwk: Mapped[str] = mapped_column(
        Text, nullable=False, default=generate_signature_jwk_string
    )
    registration_allowed: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    theme_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(Theme.id, ondelete="SET NULL"), nullable=True
    )
    theme: Mapped[Theme | None] = relationship("Theme")

    logo_url: Mapped[str | None] = mapped_column(
        String(length=512), default=None, nullable=True
    )

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name}, slug={self.slug}, default={self.default})"

    def get_sign_jwk(self) -> jwk.JWK:
        return load_jwk(self.sign_jwk)

    def get_host(self, domain: str) -> str:
        host = f"https://{domain}"
        if not self.default:
            host += f"/{self.slug}"
        return host

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        if not self.default:
            path_params["tenant_slug"] = self.slug
        return request.url_for(name, **path_params)

    def url_path_for(self, request: Request, name: str, **path_params: Any) -> str:
        if not self.default:
            path_params["tenant_slug"] = self.slug
        router: Router = request.scope["router"]
        return str(router.url_path_for(name, **path_params))
