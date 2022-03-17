from typing import Any

from fastapi import Request
from jwcrypto import jwk
from sqlalchemy import Boolean, Column, String, Text

from fief.crypto.jwk import generate_signature_jwk_string, load_jwk
from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Tenant(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "tenants"

    name: str = Column(String(length=255), nullable=False)
    slug: str = Column(String(length=255), nullable=False, unique=True)
    default: bool = Column(Boolean, default=False, nullable=False)
    sign_jwk: str = Column(Text, nullable=False, default=generate_signature_jwk_string)

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
