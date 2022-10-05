import logging
import sys
import uuid
from asyncio import AbstractEventLoop
from datetime import timezone
from typing import AsyncContextManager, Callable, Dict, Literal, Optional

from loguru import logger
from loguru._logger import Logger
from pydantic import UUID4

from fief.db import AsyncSession
from fief.models import AuditLog, AuditLogMessage, Workspace
from fief.models.generics import M_UUID
from fief.repositories import WorkspaceRepository
from fief.settings import settings

LOG_LEVEL = settings.log_level

STDOUT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> - "
    "{extra}"
)


class AuditLogger:
    def __init__(
        self,
        logger: Logger,
        workspace_id: uuid.UUID,
        *,
        admin_user_id: Optional[UUID4] = None,
        admin_api_key_id: Optional[UUID4] = None,
    ) -> None:
        self.logger = logger.bind(audit=True, workspace_id=str(workspace_id))
        self.admin_user_id = admin_user_id
        self.admin_api_key_id = admin_api_key_id

    def __call__(
        self,
        message: AuditLogMessage,
        *,
        level="INFO",
        subject_user_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> None:
        self.logger.log(
            level,
            message,
            subject_user_id=subject_user_id,
            admin_user_id=self.admin_user_id,
            admin_api_key_id=self.admin_api_key_id,
            **kwargs,
        )

    def log_object_write(
        self,
        operation: Literal[
            AuditLogMessage.OBJECT_CREATED,
            AuditLogMessage.OBJECT_UPDATED,
            AuditLogMessage.OBJECT_DELETED,
        ],
        object: M_UUID,
        subject_user_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> None:
        return self(
            operation,
            object_id=str(object.id),
            object_class=type(object).__name__,
            subject_user_id=subject_user_id,
            **kwargs,
        )


class DatabaseAuditLogSink:
    def __init__(
        self,
        get_main_session: Callable[..., AsyncContextManager[AsyncSession]],
        get_workspace_session: Callable[..., AsyncContextManager[AsyncSession]],
    ):
        self.get_main_session = get_main_session
        self.get_workspace_session = get_workspace_session

    async def __call__(self, message):
        record: Dict = message.record
        extra: Dict = record["extra"]
        workspace_id = extra.get("workspace_id")

        if workspace_id is None:
            return

        workspace = await self._get_workspace(uuid.UUID(workspace_id))

        if workspace is None:
            return

        async with self.get_workspace_session(workspace) as session:
            extra.pop("workspace_id")
            extra.pop("audit")
            subject_user_id = extra.pop("subject_user_id", None)
            object_id = extra.pop("object_id", None)
            object_class = extra.pop("object_class", None)
            admin_user_id = extra.pop("admin_user_id", None)
            admin_api_key_id = extra.pop("admin_api_key_id", None)
            log = AuditLog(
                timestamp=record["time"].astimezone(timezone.utc),
                level=record["level"].name,
                message=record["message"],
                subject_user_id=subject_user_id,
                object_id=object_id,
                object_class=object_class,
                admin_user_id=admin_user_id,
                admin_api_key_id=admin_api_key_id,
                extra=extra,
            )
            session.add(log)
            await session.commit()

    async def _get_workspace(self, workspace_id: uuid.UUID) -> Optional[Workspace]:
        async with self.get_main_session() as session:
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


def init_audit_logger(
    get_main_session: Callable[..., AsyncContextManager[AsyncSession]],
    get_workspace_session: Callable[..., AsyncContextManager[AsyncSession]],
    loop: Optional[AbstractEventLoop] = None,
):
    """
    Initialize the audit logger.

    Needs to be deferred because it relies on a running event loop.
    """
    logger.add(
        DatabaseAuditLogSink(get_main_session, get_workspace_session),
        level=LOG_LEVEL,
        enqueue=True,
        loop=loop,
        filter=lambda r: r["extra"].get("audit") is True,
    )


__all__ = ["init_audit_logger", "logger", "Logger"]
