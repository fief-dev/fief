from unittest.mock import MagicMock

import pytest

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import WorkspaceRepository
from fief.tasks.count_users import CountUsersTask, CountUsersWorkspaceTask
from tests.data import TestData


@pytest.mark.asyncio
class TestTasksCountUsersWorkspace:
    async def test_count_users_workspace(
        self,
        main_session_manager,
        workspace_session_manager,
        main_session: AsyncSession,
        workspace: Workspace,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        count_users_workspace = CountUsersWorkspaceTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )
        await count_users_workspace.run(str(workspace.id))

        workspace_repository = WorkspaceRepository(main_session)
        updated_workspace = await workspace_repository.get_by_id(workspace.id)
        assert updated_workspace is not None
        assert updated_workspace.users_count == len(test_data["users"])


@pytest.mark.asyncio
class TestTasksCountUsers:
    async def test_count_users(
        self, main_session_manager, workspace_session_manager, send_task_mock: MagicMock
    ):
        count_users = CountUsersTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )
        await count_users.run()

        send_task_mock.assert_called()
