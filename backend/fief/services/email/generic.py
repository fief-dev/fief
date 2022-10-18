import smtplib, ssl
from email.message import EmailMessage
from typing import Optional, Tuple
from fief.services.email.base import (
    EmailProvider,
    SendEmailError,
    format_address,
)


class Generic(EmailProvider):
    def __init__(
        self, host: str, username: str, password: str, port: int = 587
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port

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
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = format_address(from_email, from_name)
            message["To"] = format_address(to_email, to_name)
            message.set_content(text)
            message.add_alternative(html, subtype="html")

            # TODO: Cope with multiple setups? Not just TLS?
            context = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.send_message(message)
        except Exception as e:
            # TODO: This catch is too broad, what exceptions can we expect to see here?
            raise SendEmailError(str(e)) from e
