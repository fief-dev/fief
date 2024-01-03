import contextlib
from collections.abc import AsyncGenerator
from typing import Any, TypedDict

from fastapi import FastAPI

from fief import __version__
from fief.db.main import create_main_async_session_maker, create_main_engine
from fief.logger import init_logger, logger
from fief.services.posthog import get_server_id, get_server_properties, posthog
from fief.settings import settings


class LifespanState(TypedDict):
    main_async_session_maker: Any
    server_id: str


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[LifespanState, None]:
    init_logger()

    main_engine = create_main_engine()

    logger.info("Fief Server started", version=__version__)

    if settings.telemetry_enabled:
        logger.warning(
            "Telemetry is enabled.\n"
            "We will collect data to better understand how Fief is used and improve the project.\n"
            "You can opt-out by setting the environment variable `TELEMETRY_ENABLED=false`.\n"
            "Read more about Fief's telemetry here: https://docs.fief.dev/telemetry"
        )
        posthog.group_identify(
            "server", get_server_id(), properties=get_server_properties()
        )

    yield {
        "main_async_session_maker": create_main_async_session_maker(main_engine),
        "server_id": get_server_id(),
    }

    await main_engine.dispose()

    logger.info("Fief Server stopped")
