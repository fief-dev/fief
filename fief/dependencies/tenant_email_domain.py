from fastapi import Depends

from fief.dependencies.email_provider import get_email_provider
from fief.dependencies.repositories import get_repository
from fief.repositories import EmailDomainRepository, TenantRepository
from fief.services.email import EmailProvider
from fief.services.tenant_email_domain import TenantEmailDomain
from fief.settings import settings


async def get_tenant_email_domain(
    tenant_repository: TenantRepository = Depends(TenantRepository),
    email_domain_repository: EmailDomainRepository = Depends(
        get_repository(EmailDomainRepository)
    ),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> TenantEmailDomain:
    return TenantEmailDomain(
        email_provider,
        settings.email_provider,
        tenant_repository,
        email_domain_repository,
    )
