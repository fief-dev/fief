import uuid
from typing import Optional

from fastapi import Depends

from fief.dependencies.current_workspace import get_current_workspace
from fief.logger import Logger, logger
from fief.models import AuditLogMessage, Workspace


class AuditLogger:
    def __init__(self, logger: Logger, workspace_id: uuid.UUID) -> None:
        self.logger = logger.bind(audit=True, workspace_id=str(workspace_id))

    def __call__(
        self,
        message: AuditLogMessage,
        *,
        level="INFO",
        author_user_id: Optional[uuid.UUID] = None,
        subject_user_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> None:
        extra = kwargs.copy()
        if author_user_id is not None:
            extra["author_user_id"] = author_user_id
        if subject_user_id is not None:
            extra["subject_user_id"] = subject_user_id
        self.logger.log(level, message, **extra)


async def get_audit_logger(
    workspace: Workspace = Depends(get_current_workspace),
) -> AuditLogger:
    return AuditLogger(logger, workspace.id)  # type: ignore
