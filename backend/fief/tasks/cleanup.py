from typing import List, Type

import dramatiq

from fief.logger import logger
from fief.repositories import (
    AuthorizationCodeRepository,
    LoginSessionRepository,
    OAuthSessionRepository,
    RefreshTokenRepository,
    RegistrationSessionRepository,
    SessionTokenRepository,
    WorkspaceRepository,
)
from fief.repositories.base import ExpiresAtMixin
from fief.services.workspace_db import WorkspaceDatabase
from fief.tasks.base import TaskBase

repository_classes: List[Type[ExpiresAtMixin]] = [
    AuthorizationCodeRepository,
    LoginSessionRepository,
    OAuthSessionRepository,
    RefreshTokenRepository,
    RegistrationSessionRepository,
    SessionTokenRepository,
]


class CleanupTask(TaskBase):
    __name__ = "cleanup"

    async def run(self):
        latest_revision = WorkspaceDatabase().get_latest_revision()
        async with self.get_main_session() as session:
            workspace_repository = WorkspaceRepository(session)
            workspaces = await workspace_repository.all()
            for workspace in workspaces:
                if workspace.alembic_revision != latest_revision:
                    continue
                try:
                    async with self.get_workspace_session(
                        workspace
                    ) as workspace_session:
                        for repository_class in repository_classes:
                            repository = repository_class(workspace_session)
                            await repository.delete_expired()
                except ConnectionError:
                    logger.warning(
                        "Could not connect to workspace", workspace_id=str(workspace.id)
                    )


cleanup = dramatiq.actor(CleanupTask())
