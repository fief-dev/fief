import pytest

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import WorkspaceRepository
from fief.tasks.count_users import CountUsersTask
from tests.data import TestData


@pytest.mark.asyncio
class TestTasksCountUsers:
    async def test_count_users(
        self,
        main_session_manager,
        workspace_session_manager,
        main_session: AsyncSession,
        workspace: Workspace,
        test_data: TestData,
    ):
        count_users = CountUsersTask(main_session_manager, workspace_session_manager)
        await count_users.run()

        workspace_repository = WorkspaceRepository(main_session)
        updated_workspace = await workspace_repository.get_by_id(workspace.id)
        assert updated_workspace is not None
        assert updated_workspace.users_count == len(test_data["users"])
