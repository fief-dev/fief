from typing import Optional, Tuple

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from fief.services.email.base import EmailProvider, SendEmailError, format_address


class Sendgrid(EmailProvider):
    def __init__(self, server_token: str) -> None:
        self._client = SendGridAPIClient(api_key=server_token)

    def send_email(
        self,
        *,
        sender: Tuple[str, Optional[str]],
        recipient: Tuple[str, Optional[str]],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
    ):
        from_email, from_name = sender
        to_email, to_name = recipient
        try:
            message = Mail(
                from_email=format_address(from_email, from_name),
                to_emails=format_address(to_email, to_name),
                subject=subject,
                html_content=text)

            self._client.send(message)

        except Exception as e:
            raise SendEmailError(str(e)) from e
