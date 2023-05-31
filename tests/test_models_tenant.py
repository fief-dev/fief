from fief.models import EmailDomain, Tenant
from fief.settings import settings
from tests.data import TestData


def get_tenant(
    *,
    from_email: str | None = None,
    from_name: str | None = None,
    email_domain: EmailDomain | None = None,
) -> Tenant:
    return Tenant(
        name="Default",
        slug="default",
        default=True,
        oauth_providers=[],
        email_from_email=from_email,
        email_from_name=from_name,
        email_domain=email_domain,
    )


class TestGetEmailSender:
    def test_no_from(self):
        tenant = get_tenant()

        assert tenant.get_email_sender() == (
            settings.default_from_email,
            settings.default_from_name,
        )

    def test_no_email_domain(self):
        tenant = get_tenant(from_email="anne@bretagne.duchy", from_name="Anne")

        assert tenant.get_email_sender() == ("anne@bretagne.duchy", "Anne")

    def test_email_domain_not_verified(self, test_data: TestData):
        email_domain = test_data["email_domains"]["bretagne.duchy"]
        tenant = get_tenant(
            from_email="anne@bretagne.duchy",
            from_name="Anne",
            email_domain=email_domain,
        )

        assert tenant.get_email_sender() == (settings.default_from_email, "Anne")

    def test_email_domain_verified(self, test_data: TestData):
        email_domain = test_data["email_domains"]["bretagne.duchy"]
        email_domain.records = [
            record.copy(update={"verified": True}).dict()  # type: ignore
            for record in email_domain.records
        ]
        tenant = get_tenant(
            from_email="anne@bretagne.duchy",
            from_name="Anne",
            email_domain=email_domain,
        )

        assert tenant.get_email_sender() == ("anne@bretagne.duchy", "Anne")
