import contextlib
import functools
from collections.abc import AsyncGenerator
from typing import TypedDict

from fastapi import FastAPI

from fief import __version__
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.dependencies.db import main_async_session_maker
from fief.logger import init_audit_logger, logger


class LifespanState(TypedDict):
    workspace_engine_manager: WorkspaceEngineManager


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[LifespanState, None]:
    workspace_engine_manager = WorkspaceEngineManager()

    init_audit_logger(
        main_async_session_maker,
        functools.partial(
            get_workspace_session, workspace_engine_manager=workspace_engine_manager
        ),
    )
    logger.info("Fief Server started", version=__version__)

    yield {"workspace_engine_manager": workspace_engine_manager}

    await workspace_engine_manager.close_all()
