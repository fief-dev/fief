from fief.services.email.base import EmailDomain, EmailProvider


class Null(EmailProvider):
    DOMAIN_AUTHENTICATION = False

    def send_email(
        self,
        *,
        sender: tuple[str, str | None],
        recipient: tuple[str, str | None],
        subject: str,
        html: str | None = None,
        text: str | None = None,
    ):
        return

    def create_domain(self, domain: str) -> EmailDomain:
        raise NotImplementedError()

    def verify_domain(self, email_domain: EmailDomain) -> EmailDomain:
        raise NotImplementedError()
