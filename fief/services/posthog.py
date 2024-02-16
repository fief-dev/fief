import functools
import hashlib
from typing import Any

from posthog import Posthog

from fief import __version__
from fief.db import AsyncSession
from fief.repositories.user import UserRepository
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
    domain = settings.fief_domain
    server_id_hash = hashlib.sha256()
    server_id_hash.update(domain.encode("utf-8"))
    server_id_hash.update(settings.secret.get_secret_value().encode("utf-8"))
    return server_id_hash.hexdigest()


async def get_server_properties(session: AsyncSession) -> dict[str, Any]:
    user_repository = UserRepository(session)
    users_count = await user_repository.count_all()
    return {
        "version": __version__,
        "is_localhost": is_localhost(settings.fief_domain),
        "database_type": settings.database_type,
        "users_count": users_count,
    }
