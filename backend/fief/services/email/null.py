from typing import Optional, Tuple

from fief.services.email.base import EmailProvider


class Null(EmailProvider):
    def send_email(
        self,
        *,
        sender: Tuple[str, Optional[str]],
        recipient: Tuple[str, Optional[str]],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
    ):
        return
