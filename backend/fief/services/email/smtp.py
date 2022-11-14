import smtplib
import ssl
from email.message import EmailMessage

from fief.services.email.base import EmailProvider, SendEmailError, format_address


class SMTP(EmailProvider):
    def __init__(
        self,
        host: str,
        username: str | None = None,
        password: str | None = None,
        port: int = 587,
        ssl: bool | None = True,
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.ssl = ssl

    def send_email(
        self,
        *,
        sender: tuple[str, str | None],
        recipient: tuple[str, str | None],
        subject: str,
        html: str | None = None,
        text: str | None = None,
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
