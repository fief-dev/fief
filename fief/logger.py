import json
import logging
import sys
import uuid
from datetime import UTC
from typing import TYPE_CHECKING, Literal

from loguru import logger
from pydantic import UUID4

from fief.models import AuditLogMessage
from fief.models.generics import M_UUID
from fief.settings import settings

if TYPE_CHECKING:
    from dramatiq import Actor
    from loguru import Logger, Message, Record

LOG_LEVEL = settings.log_level


def stdout_format(record: "Record") -> str:
    record["extra"]["extra_json"] = json.dumps(record["extra"])
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> - "
        "{extra[extra_json]}"
        "\n{exception}"
    )


class AuditLogger:
    def __init__(
        self,
        logger: "Logger",
        *,
        admin_user_id: UUID4 | None = None,
        admin_api_key_id: UUID4 | None = None,
    ) -> None:
        self.logger = logger.bind(audit=True)
        self.admin_user_id = admin_user_id
        self.admin_api_key_id = admin_api_key_id

    def __call__(
        self,
        message: AuditLogMessage,
        *,
        level="INFO",
        subject_user_id: uuid.UUID | None = None,
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
        subject_user_id: uuid.UUID | None = None,
        **kwargs,
    ) -> None:
        return self(
            operation,
            object_id=str(object.id),
            object_class=type(object).__name__,
            subject_user_id=subject_user_id,
            **kwargs,
        )


class AuditLogSink:
    def __init__(self, task: "Actor") -> None:
        self.task = task

    async def __call__(self, message: "Message"):
        record: "Record" = message.record
        self.task.send(
            json.dumps(
                {
                    "time": record["time"].astimezone(UTC).isoformat(),
                    "level": record["level"].name,
                    "message": record["message"],
                    "extra": record["extra"],
                },
                cls=AuditLogSink.Encoder,
            ),
        )

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return json.JSONEncoder.default(self, obj)


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


def init_logger():
    from fief.tasks import write_audit_log

    logger.remove()
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format=stdout_format,
        filter=lambda record: "audit" not in record["extra"],
    )
    logger.add(
        AuditLogSink(write_audit_log),
        level=LOG_LEVEL,
        filter=lambda r: r["extra"].get("audit") is True,
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


__all__ = ["init_logger", "logger"]
