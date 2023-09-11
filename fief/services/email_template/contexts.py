from typing import Any

from pydantic import BaseModel, ConfigDict

from fief.db import AsyncSession
from fief.repositories import TenantRepository, UserRepository
from fief.schemas.tenant import Tenant
from fief.schemas.user import UserEmailContext
from fief.services.email_template.types import EmailTemplateType


class EmailContext(BaseModel):
    tenant: Tenant
    user: UserEmailContext
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def create_sample_context(cls, session: AsyncSession):
        context_kwargs = await cls._get_sample_context_kwargs(session)
        return cls(**context_kwargs)

    @classmethod
    async def _get_sample_context_kwargs(cls, session: AsyncSession) -> dict[str, Any]:
        context_kwargs: dict[str, Any] = {}
        tenant_repository = TenantRepository(session)
        tenant = await tenant_repository.get_default()
        assert tenant is not None
        context_kwargs["tenant"] = tenant

        user_repository = UserRepository(session)
        user = await user_repository.get_one_by_tenant(tenant.id)
        if user is None:
            context_kwargs["user"] = UserEmailContext.create_sample(tenant)
        else:
            context_kwargs["user"] = user

        return context_kwargs


class WelcomeContext(EmailContext):
    pass


class VerifyEmailContext(EmailContext):
    code: str

    @classmethod
    async def _get_sample_context_kwargs(cls, session: AsyncSession) -> dict[str, Any]:
        context_kwargs = await super()._get_sample_context_kwargs(session)
        context_kwargs["code"] = "ABC123"
        return context_kwargs


class ForgotPasswordContext(EmailContext):
    reset_url: str

    @classmethod
    async def _get_sample_context_kwargs(cls, session: AsyncSession) -> dict[str, Any]:
        context_kwargs = await super()._get_sample_context_kwargs(session)
        context_kwargs["reset_url"] = "https://example.fief.dev/reset"
        return context_kwargs


EMAIL_TEMPLATE_CONTEXT_CLASS_MAP: dict[EmailTemplateType, type[EmailContext]] = {
    EmailTemplateType.BASE: EmailContext,
    EmailTemplateType.WELCOME: WelcomeContext,
    EmailTemplateType.VERIFY_EMAIL: VerifyEmailContext,
    EmailTemplateType.FORGOT_PASSWORD: ForgotPasswordContext,
}
