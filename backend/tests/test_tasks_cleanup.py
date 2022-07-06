import pytest

from fief.tasks.cleanup import CleanupTask


@pytest.mark.asyncio
class TestTasksCleanup:
    async def test_cleanup(self, main_session_manager, workspace_session_manager):
        cleanup = CleanupTask(main_session_manager, workspace_session_manager)
        await cleanup.run()
