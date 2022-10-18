from enum import Enum
from typing import Dict, Type

from fief.services.email.base import EmailError, EmailProvider, SendEmailError
from fief.services.email.null import Null
from fief.services.email.postmark import Postmark
from fief.services.email.smtp import SMTP


class AvailableEmailProvider(str, Enum):
    NULL = "NULL"
    POSTMARK = "POSTMARK"
    SMTP = "SMTP"


EMAIL_PROVIDERS: Dict[AvailableEmailProvider, Type[EmailProvider]] = {
    AvailableEmailProvider.NULL: Null,
    AvailableEmailProvider.POSTMARK: Postmark,
    AvailableEmailProvider.SMTP: SMTP,
}

__all__ = [
    "AvailableEmailProvider",
    "EMAIL_PROVIDERS",
    "EmailError",
    "EmailProvider",
    "SendEmailError",
]
