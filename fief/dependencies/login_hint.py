import urllib.parse
import uuid

from email_validator import EmailNotValidError, validate_email
from fastapi import Cookie, Depends

from fief.dependencies.oauth_provider import get_oauth_providers
from fief.models import OAuthProvider
from fief.settings import settings

LoginHint = str | OAuthProvider


async def get_login_hint(
    login_hint: str | None = Cookie(None, alias=settings.login_hint_cookie_name),
    oauth_providers: list[OAuthProvider] = Depends(get_oauth_providers),
) -> LoginHint | None:
    if login_hint is None:
        return None

    unquoted_login_hint = urllib.parse.unquote(login_hint)

    try:
        validated_email = validate_email(
            unquoted_login_hint, check_deliverability=False
        )
    except EmailNotValidError:
        pass
    else:
        return validated_email.normalized

    try:
        oauth_provider_id = uuid.UUID(unquoted_login_hint)
        for oauth_provider in oauth_providers:
            if oauth_provider.id == oauth_provider_id:
                return oauth_provider
    except ValueError:
        pass

    return None
