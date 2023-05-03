import contextlib
from collections.abc import AsyncGenerator
from typing import TypedDict

from fastapi import FastAPI

from fief import __version__
from fief.db.workspace import WorkspaceEngineManager
from fief.logger import init_logger, logger
from fief.services.posthog import get_server_id, get_server_properties, posthog
from fief.settings import settings


class LifespanState(TypedDict):
    workspace_engine_manager: WorkspaceEngineManager
    server_id: str


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[LifespanState, None]:
    init_logger()

    workspace_engine_manager = WorkspaceEngineManager()

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
        "workspace_engine_manager": workspace_engine_manager,
        "server_id": get_server_id(),
    }

    await workspace_engine_manager.close_all()
