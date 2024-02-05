from collections.abc import Mapping
from typing import Any

import asgi_babel
import wtforms.i18n
from asgi_tools import Request
from babel import Locale, UnknownLocaleError, support

from fief.paths import LOCALE_DIRECTORY
from fief.settings import settings

Translations = support.Translations


async def select_locale(request: Request) -> str | None:
    user_locale_cookie = request.cookies.get(settings.user_locale_cookie_name)
    if user_locale_cookie is not None:
        try:
            Locale.parse(user_locale_cookie, sep="-")
        except (ValueError, UnknownLocaleError):
            pass
        else:
            return user_locale_cookie
    return await asgi_babel.select_locale_by_request(request)


class BabelMiddleware(asgi_babel.BabelMiddleware):
    def __post_init__(self):
        self.locale_selector = select_locale
        return super().__post_init__()


def get_babel_middleware_kwargs() -> Mapping[str, Any]:
    return dict(locales_dirs=[LOCALE_DIRECTORY, wtforms.i18n.messages_path()])
