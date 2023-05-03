import sentry_dramatiq
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration

from fief import __version__
from fief.logger import init_logger, logger
from fief.settings import settings

sentry_sdk.init(
    dsn=settings.sentry_dsn_worker,
    environment=settings.environment.value,
    release=__version__,
    integrations=[sentry_dramatiq.DramatiqIntegration(), RedisIntegration()],
)

from fief import tasks  # noqa: E402

init_logger()
logger.info("Fief Worker started", version=__version__)

__all__ = ["tasks"]
