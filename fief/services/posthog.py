import functools
import hashlib
from typing import TYPE_CHECKING, Any

from posthog import Posthog

from fief import __version__
from fief.services.localhost import is_localhost
from fief.settings import settings

if TYPE_CHECKING:
    from fief.models import Workspace

posthog = Posthog(
    "__POSTHOG_API_KEY__",
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


def get_workspace_properties(workspace: "Workspace") -> dict[str, Any]:
    return {
        "server": get_server_id(),
        "users_count": workspace.users_count,
        "byod": workspace.database_type is not None,
        "database_type": workspace.database_type,
    }
