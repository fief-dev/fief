import contextlib
import logging
import sys
import uuid
from asyncio import AbstractEventLoop
from datetime import timezone
from typing import Dict, Optional

from loguru import logger
from loguru._logger import Logger

from fief.db.main import get_main_async_session
from fief.db.workspace import get_workspace_session
from fief.models import AuditLog, Workspace
from fief.repositories import WorkspaceRepository
from fief.settings import settings

LOG_LEVEL = settings.log_level

STDOUT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> - "
    "{extra}"
)


class DatabaseAuditLogSink:
    async def __call__(self, message):
        record: Dict = message.record
        extra: Dict = record["extra"]
        workspace_id = extra.get("workspace_id")

        if workspace_id is None:
            return

        workspace = await self._get_workspace(uuid.UUID(workspace_id))

        if workspace is None:
            return

        async with get_workspace_session(workspace) as session:
            extra.pop("workspace_id")
            extra.pop("audit")
            author_user_id = extra.pop("author_user_id", None)
            subject_user_id = extra.pop("subject_user_id", None)
            log = AuditLog(
                timestamp=record["time"].astimezone(timezone.utc),
                level=record["level"].name,
                message=record["message"],
                author_user_id=author_user_id,
                subject_user_id=subject_user_id,
                extra=extra,
            )
            session.add(log)
            await session.commit()

    async def _get_workspace(self, workspace_id: uuid.UUID) -> Optional[Workspace]:
        async with contextlib.asynccontextmanager(get_main_async_session)() as session:
            repository = WorkspaceRepository(session)
            return await repository.get_by_id(workspace_id)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logger.configure(
    handlers=[
        dict(
            sink=sys.stdout,
            level=LOG_LEVEL,
            format=STDOUT_FORMAT,
            filter=lambda record: "audit" not in record["extra"],
        )
    ],
)

logging.basicConfig(handlers=[InterceptHandler()], level=LOG_LEVEL, force=True)
for uvicorn_logger_name in ["uvicorn", "uvicorn.error"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.setLevel(LOG_LEVEL)
    uvicorn_logger.handlers = []
for uvicorn_logger_name in ["uvicorn.access"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.setLevel(LOG_LEVEL)
    uvicorn_logger.handlers = [InterceptHandler()]


def init_audit_logger(loop: Optional[AbstractEventLoop] = None):
    """
    Initialize the audit logger.

    Needs to be deferred because it relies on a running event loop.
    """
    logger.add(
        DatabaseAuditLogSink(),
        level=LOG_LEVEL,
        enqueue=True,
        loop=loop,
        filter=lambda r: r["extra"].get("audit") is True,
    )


__all__ = ["init_audit_logger", "logger", "Logger"]
