from typing import Protocol


class EmailProvider(Protocol):
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


class EmailError(Exception):
    def __init__(self, message: str):
        self.message = message


class SendEmailError(EmailError):
    pass


def format_address(email: str, name: str | None = None):
    return email if name is None else f"{name} <{email}>"
