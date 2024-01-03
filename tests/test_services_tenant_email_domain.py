from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from fief.db import AsyncSession
from fief.repositories import EmailDomainRepository, TenantRepository
from fief.services.email import (
    AvailableEmailProvider,
    CreateDomainError,
    EmailDomain,
    EmailDomainDNSRecord,
    EmailProvider,
    VerifyDomainError,
)
from fief.services.tenant_email_domain import (
    DomainAuthenticationNotImplementedError,
    TenantEmailDomain,
    TenantEmailDomainError,
    TenantHasNoEmailDomainError,
    TenantHasNoFromEmailAddressError,
)
from tests.data import TestData


@pytest.fixture
def email_provider_without_domain_authentication():
    mock = MagicMock(spec=EmailProvider)
    mock.DOMAIN_AUTHENTICATION = False
    return mock


@pytest.fixture
def email_provider():
    mock = MagicMock(spec=EmailProvider)
    mock.DOMAIN_AUTHENTICATION = True
    return mock


GetTenantEmailDomain = Callable[[EmailProvider], TenantEmailDomain]


@pytest.fixture
def get_tenant_email_domain(main_session: AsyncSession) -> GetTenantEmailDomain:
    tenant_repository = TenantRepository(main_session)
    email_domain_repository = EmailDomainRepository(main_session)

    def _get_tenant_email_domain(email_provider: EmailProvider) -> TenantEmailDomain:
        return TenantEmailDomain(
            email_provider,
            AvailableEmailProvider.NULL,
            tenant_repository,
            email_domain_repository,
        )

    return _get_tenant_email_domain


@pytest.mark.asyncio
class TestAuthenticateDomain:
    async def test_domain_authentication_not_implemented(
        self,
        test_data: TestData,
        email_provider_without_domain_authentication: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant_email_domain = get_tenant_email_domain(
            email_provider_without_domain_authentication
        )
        with pytest.raises(DomainAuthenticationNotImplementedError):
            await tenant_email_domain.authenticate_domain(tenant)

    async def test_no_from_email_address(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant_email_domain = get_tenant_email_domain(email_provider)
        with pytest.raises(TenantHasNoFromEmailAddressError):
            await tenant_email_domain.authenticate_domain(tenant)

    async def test_already_existing_domain(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
        main_session: AsyncSession,
    ):
        tenant = test_data["tenants"]["default"]
        main_session.add(
            tenant
        )  # Trick to make tenant "editable" in the main_session context
        tenant.email_domain = None
        tenant.email_from_email = "anne@bretagne.duchy"

        tenant_email_domain = get_tenant_email_domain(email_provider)
        tenant = await tenant_email_domain.authenticate_domain(tenant)
        assert tenant.email_domain_id is not None
        assert tenant.email_domain_id == test_data["email_domains"]["bretagne.duchy"].id

    async def test_create_domain_error(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant.email_from_email = "anne@nantes.city"

        email_provider.create_domain.side_effect = CreateDomainError("Error")

        tenant_email_domain = get_tenant_email_domain(email_provider)
        with pytest.raises(TenantEmailDomainError, match="Error"):
            await tenant_email_domain.authenticate_domain(tenant)

    async def test_new_domain(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant.email_from_email = "anne@nantes.city"

        email_provider.create_domain.return_value = EmailDomain(
            domain_id="5678",
            domain="nantes.city",
            records=[
                EmailDomainDNSRecord(
                    id="dkim",
                    type="CNAME",
                    host="email.nantes.city",
                    value="DKIM_KEY",
                    verified=False,
                )
            ],
        )

        tenant_email_domain = get_tenant_email_domain(email_provider)
        tenant = await tenant_email_domain.authenticate_domain(tenant)

        assert tenant.email_domain is not None
        assert tenant.email_domain.domain_id == "5678"


@pytest.mark.asyncio
class TestVerifyDomain:
    async def test_domain_authentication_not_implemented(
        self,
        test_data: TestData,
        email_provider_without_domain_authentication: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant_email_domain = get_tenant_email_domain(
            email_provider_without_domain_authentication
        )
        with pytest.raises(DomainAuthenticationNotImplementedError):
            await tenant_email_domain.verify_domain(tenant)

    async def test_no_email_domain(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant.email_domain = None

        tenant_email_domain = get_tenant_email_domain(email_provider)
        with pytest.raises(TenantHasNoEmailDomainError):
            await tenant_email_domain.verify_domain(tenant)

    async def test_verify_error(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant.email_domain = test_data["email_domains"]["bretagne.duchy"]

        email_provider.verify_domain.side_effect = VerifyDomainError("Error")

        tenant_email_domain = get_tenant_email_domain(email_provider)
        with pytest.raises(TenantEmailDomainError, match="Error"):
            await tenant_email_domain.verify_domain(tenant)

    async def test_verify_success(
        self,
        test_data: TestData,
        email_provider: MagicMock,
        get_tenant_email_domain: GetTenantEmailDomain,
    ):
        tenant = test_data["tenants"]["default"]
        tenant.email_domain = test_data["email_domains"]["bretagne.duchy"]

        email_provider.verify_domain.return_value = EmailDomain(
            domain_id="1234",
            domain="bretagne.duchy",
            records=[
                EmailDomainDNSRecord(
                    id="dkim",
                    type="CNAME",
                    host="bretagne.duchy",
                    value="DKIM_KEY",
                    verified=True,
                )
            ],
        )

        tenant_email_domain = get_tenant_email_domain(email_provider)
        tenant = await tenant_email_domain.verify_domain(tenant)
        assert tenant.email_domain is not None
        assert tenant.email_domain.is_verified()
