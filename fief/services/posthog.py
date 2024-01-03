import functools
import hashlib
from typing import Any

from posthog import Posthog

from fief import __version__
from fief.services.localhost import is_localhost
from fief.settings import settings

POSTHOG_API_KEY = "__POSTHOG_API_KEY__"

posthog = Posthog(
    POSTHOG_API_KEY,
    host="https://eu.posthog.com",
    disabled=not settings.telemetry_enabled,
)


@functools.cache
def get_server_id() -> str:
    domain = settings.root_domain
    if domain == "fief.dev":
        return domain
    server_id_hash = hashlib.sha256()
    server_id_hash.update(domain.encode("utf-8"))
    server_id_hash.update(settings.secret.get_secret_value().encode("utf-8"))
    return server_id_hash.hexdigest()


@functools.cache
def get_server_properties() -> dict[str, Any]:
    return {
        "version": __version__,
        "is_localhost": is_localhost(settings.root_domain),
        "database_type": settings.database_type,
    }
