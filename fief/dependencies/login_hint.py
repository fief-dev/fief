import urllib.parse
import uuid

from fastapi import Cookie
from pydantic import UUID4, EmailError, EmailStr

from fief.settings import settings

LoginHint = str | UUID4


async def get_login_hint(
    login_hint: str | None = Cookie(None, alias=settings.login_hint_cookie_name)
) -> LoginHint | None:
    if login_hint is None:
        return None

    unquoted_login_hint = urllib.parse.unquote(login_hint)

    try:
        return EmailStr.validate(unquoted_login_hint)
    except EmailError:
        pass

    try:
        return uuid.UUID(unquoted_login_hint)
    except ValueError:
        pass

    return None
