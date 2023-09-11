import dataclasses

import email_validator

from fief.models import EmailDomain, Tenant
from fief.repositories import EmailDomainRepository, TenantRepository
from fief.services.email import (
    AvailableEmailProvider,
    CreateDomainError,
    EmailProvider,
    VerifyDomainError,
)
from fief.services.email import (
    EmailDomain as EmailDomainData,
)
from fief.services.email import (
    EmailDomainDNSRecord as EmailDomainDNSRecordData,
)


def email_domain_dataclass_to_model(
    data: EmailDomainData, email_provider: AvailableEmailProvider
) -> EmailDomain:
    data_dict = dataclasses.asdict(data)
    records = data_dict.pop("records")
    email_domain = EmailDomain(email_provider=email_provider, **data_dict)
    email_domain.records = records
    return email_domain


def email_domain_model_to_dataclass(model: EmailDomain) -> EmailDomainData:
    return EmailDomainData(
        domain_id=model.domain_id,
        domain=model.domain,
        records=[
            EmailDomainDNSRecordData(**record.model_dump()) for record in model.records
        ],
    )


class TenantEmailDomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TenantHasNoFromEmailAddressError(TenantEmailDomainError):
    def __init__(self):
        super().__init__("Tenant doesn't have a from email address specified.")


class TenantHasNoEmailDomainError(TenantEmailDomainError):
    def __init__(self):
        super().__init__("Tenant has no associated email domain to verify.")


class DomainAuthenticationNotImplementedError(TenantEmailDomainError):
    def __init__(self):
        super().__init__("This EmailProvider doesn't support domain authentication")


class TenantEmailDomain:
    def __init__(
        self,
        email_provider: EmailProvider,
        current_email_provider: AvailableEmailProvider,
        tenant_repository: TenantRepository,
        email_domain_repository: EmailDomainRepository,
    ) -> None:
        self.email_provider = email_provider
        self.current_email_provider = current_email_provider
        self.tenant_repository = tenant_repository
        self.email_domain_repository = email_domain_repository

    async def authenticate_domain(self, tenant: Tenant) -> Tenant:
        if not self.email_provider.DOMAIN_AUTHENTICATION:
            raise DomainAuthenticationNotImplementedError()

        if tenant.email_from_email is None:
            raise TenantHasNoFromEmailAddressError()

        validated_email = email_validator.validate_email(
            tenant.email_from_email, check_deliverability=False
        )
        domain = validated_email.domain

        email_domain = await self.email_domain_repository.get_by_domain(domain)
        if email_domain is None:
            try:
                email_domain_data = self.email_provider.create_domain(domain)
                email_domain = email_domain_dataclass_to_model(
                    email_domain_data, self.current_email_provider
                )
            except CreateDomainError as e:
                raise TenantEmailDomainError(e.message) from e
        tenant.email_domain = email_domain
        await self.tenant_repository.update(tenant)
        return tenant

    async def verify_domain(self, tenant: Tenant) -> Tenant:
        if not self.email_provider.DOMAIN_AUTHENTICATION:
            raise DomainAuthenticationNotImplementedError()

        email_domain = tenant.email_domain
        if email_domain is None:
            raise TenantHasNoEmailDomainError()

        try:
            email_domain_data = email_domain_model_to_dataclass(email_domain)
            email_domain_data = self.email_provider.verify_domain(email_domain_data)
        except VerifyDomainError as e:
            raise TenantEmailDomainError(e.message) from e

        data_dict = dataclasses.asdict(email_domain_data)
        records = data_dict.pop("records")
        email_domain.records = records
        await self.tenant_repository.update(tenant)
        return tenant
