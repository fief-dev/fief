from unittest.mock import MagicMock

import pytest

from fief.models import Workspace
from fief.tasks.cleanup import CleanupTask, CleanupWorkspaceTask


@pytest.mark.asyncio
class TestTasksWorkspaceCleanup:
    async def test_workspace_cleanup(
        self,
        main_session_manager,
        workspace_session_manager,
        send_task_mock: MagicMock,
        workspace: Workspace,
    ):
        cleanup = CleanupWorkspaceTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )
        await cleanup.run(str(workspace.id))


@pytest.mark.asyncio
class TestTasksCleanup:
    async def test_cleanup(
        self, main_session_manager, workspace_session_manager, send_task_mock: MagicMock
    ):
        cleanup = CleanupTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )
        await cleanup.run()

        send_task_mock.assert_called()
