from typing import Optional, Protocol, Tuple


class EmailProvider(Protocol):
    def send_email(
        self,
        *,
        sender: Tuple[str, Optional[str]],
        recipient: Tuple[str, Optional[str]],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
    ):
        ...

    def format_address(self, email: str, name: Optional[str] = None):
        return email if name is None else f"{name} <{email}>"


class EmailError(Exception):
    def __init__(self, message: str):
        self.message = message


class SendEmailError(EmailError):
    pass
