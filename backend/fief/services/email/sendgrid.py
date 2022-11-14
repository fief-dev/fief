from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail

from fief.services.email.base import EmailProvider, SendEmailError, format_address


class Sendgrid(EmailProvider):
    def __init__(self, api_key: str) -> None:
        self._client = SendGridAPIClient(api_key=api_key)

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
            message = Mail(
                from_email=format_address(from_email, from_name),
                to_emails=format_address(to_email, to_name),
                subject=subject,
                html_content=html,
                plain_text_content=text,
            )

            self._client.send(message)

        except SendGridException as e:
            raise SendEmailError(str(e)) from e
