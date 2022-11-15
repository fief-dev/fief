from enum import Enum

from fief.services.email.base import EmailError, EmailProvider, SendEmailError
from fief.services.email.null import Null
from fief.services.email.postmark import Postmark
from fief.services.email.sendgrid import Sendgrid
from fief.services.email.smtp import SMTP


class AvailableEmailProvider(str, Enum):
    NULL = "NULL"
    POSTMARK = "POSTMARK"
    SMTP = "SMTP"
    SENDGRID = "SENDGRID"


EMAIL_PROVIDERS: dict[AvailableEmailProvider, type[EmailProvider]] = {
    AvailableEmailProvider.NULL: Null,
    AvailableEmailProvider.POSTMARK: Postmark,
    AvailableEmailProvider.SMTP: SMTP,
    AvailableEmailProvider.SENDGRID: Sendgrid,
}

__all__ = [
    "AvailableEmailProvider",
    "EMAIL_PROVIDERS",
    "EmailError",
    "EmailProvider",
    "SendEmailError",
]
