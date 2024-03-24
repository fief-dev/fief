import asyncio

from fief_client import FiefAsync
from uvicorn.server import Server

from fief.logger import logger
from fief.settings import settings


def _is_uvicorn_ssl() -> bool:
    """
    Hacky way to determine if the Uvicorn server is running with SSL,
    by retrieving the server instance from the running asyncio tasks.
    """
    try:
        for task in asyncio.all_tasks():
            coroutine = task.get_coro()
            frame = coroutine.cr_frame
            args = frame.f_locals
            if self := args.get("self"):
                if isinstance(self, Server):
                    return self.config.is_ssl
    except RuntimeError:
        pass
    return False


_is_ssl = _is_uvicorn_ssl()
_scheme = "https" if _is_ssl else "http"
if _is_ssl:
    logger.debug("Uvicorn server is running with SSL")
else:
    logger.debug("Uvicorn server is running without SSL")

fief = FiefAsync(
    f"{_scheme}://localhost:{settings.port}",  # Always call Fief on localhost
    settings.fief_client_id,
    settings.fief_client_secret,
    encryption_key=settings.fief_encryption_key,
    host=settings.fief_domain,
    verify=False,
)


async def get_fief() -> FiefAsync:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return fief
