import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Tuple

from fief.services.email.base import EmailProvider, SendEmailError, format_address


class SMTP(EmailProvider):
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 587,
        ssl: Optional[bool] = True,
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.ssl = ssl

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
            if html is not None:
                message.add_alternative(html, subtype="html")
            if text is not None:
                message.add_alternative(text, subtype="plain")

            with smtplib.SMTP(self.host, self.port) as server:
                if self.ssl:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)
        except smtplib.SMTPException as e:
            raise SendEmailError(str(e)) from e
