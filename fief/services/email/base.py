import dataclasses
from typing import Protocol


@dataclasses.dataclass
class EmailDomainDNSRecord:
    id: str
    type: str
    host: str
    value: str
    verified: bool


@dataclasses.dataclass
class EmailDomain:
    domain_id: str
    domain: str
    records: list[EmailDomainDNSRecord]


class EmailProvider(Protocol):
    DOMAIN_AUTHENTICATION: bool

    def send_email(
        self,
        *,
        sender: tuple[str, str | None],
        recipient: tuple[str, str | None],
        subject: str,
        html: str | None = None,
        text: str | None = None,
    ):
        ...

    def create_domain(self, domain: str) -> EmailDomain:
        ...

    def verify_domain(self, email_domain: EmailDomain) -> EmailDomain:
        ...


class EmailError(Exception):
    def __init__(self, message: str):
        self.message = message


class SendEmailError(EmailError):
    pass


class CreateDomainError(EmailError):
    pass


class VerifyDomainError(EmailError):
    pass


def format_address(email: str, name: str | None = None):
    return email if name is None else f"{name} <{email}>"
