import re
from wtforms import validators

from fief.models.client import LOCALHOST_HOST_PATTERN


class RedirectURLValidator(validators.Regexp):
    def __init__(self, message=None):
        regex = (
            r"^(?P<scheme>[a-z]+)://"
            r"(?P<host>[^\/\?:]+)"
            r"(?P<port>:[0-9]+)?"
            r"(?P<path>\/.*?)?"
            r"(?P<query>\?.*)?$"
        )
        super().__init__(regex, re.IGNORECASE, message)

    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext("Invalid URL.")

        match = super().__call__(form, field, message)
        scheme = match.group("scheme")
        host = match.group("host")

        if scheme == "http" and not LOCALHOST_HOST_PATTERN.match(host):
            raise validators.ValidationError("An HTTPS URL is required.")
