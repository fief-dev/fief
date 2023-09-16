from typing import Any

from fastapi import Request
from jwcrypto import jwk
from pydantic import UUID4
from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.routing import Router

from fief.crypto.jwk import generate_signature_jwk_string, load_jwk
from fief.models.base import WorkspaceBase, get_prefixed_tablename
from fief.models.email_domain import EmailDomain
from fief.models.generics import GUID, CreatedUpdatedAt, PydanticUrlString, UUIDModel
from fief.models.oauth_provider import OAuthProvider
from fief.models.theme import Theme
from fief.settings import settings

TenantOAuthProvider = Table(
    get_prefixed_tablename("tenants_oauth_providers"),
    WorkspaceBase.metadata,
    Column(
        "tenant_id",
        ForeignKey(f"{get_prefixed_tablename('tenants')}.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "oauth_provider_id",
        ForeignKey(
            f"{get_prefixed_tablename('oauth_providers')}.id", ondelete="CASCADE"
        ),
        primary_key=True,
    ),
)


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

    application_url: Mapped[str | None] = mapped_column(
        PydanticUrlString(String)(length=512), default=None, nullable=True
    )

    theme_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(Theme.id, ondelete="SET NULL"), nullable=True
    )
    theme: Mapped[Theme | None] = relationship("Theme")

    logo_url: Mapped[str | None] = mapped_column(
        PydanticUrlString(String)(length=512), default=None, nullable=True
    )

    oauth_providers: Mapped[list[OAuthProvider]] = relationship(
        "OAuthProvider", secondary=TenantOAuthProvider, lazy="selectin"
    )

    email_from_email: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )
    email_from_name: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )
    email_domain_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(EmailDomain.id, ondelete="SET NULL"), nullable=True
    )
    email_domain: Mapped[EmailDomain | None] = relationship("EmailDomain")

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
        return str(request.url_for(name, **path_params))

    def url_path_for(self, request: Request, name: str, **path_params: Any) -> str:
        if not self.default:
            path_params["tenant_slug"] = self.slug
        router: Router = request.scope["router"]
        return str(router.url_path_for(name, **path_params))

    def get_oauth_provider(self, id: UUID4) -> OAuthProvider | None:
        for oauth_provider in self.oauth_providers:
            if oauth_provider.id == id:
                return oauth_provider
        return None

    def get_email_sender(self) -> tuple[str, str | None]:
        # Use the provided email in two cases:
        # * No associated email domain (the provider may not support it)
        # * If associated email domain, it must be verified
        valid_email_domain = (
            self.email_domain is None or self.email_domain.is_verified()
        )

        from_email = (
            self.email_from_email
            if self.email_from_email is not None and valid_email_domain
            else settings.default_from_email
        )
        from_name = (
            self.email_from_name
            if self.email_from_name is not None
            else settings.default_from_name
        )

        return (from_email, from_name)
