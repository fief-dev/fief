from unittest.mock import MagicMock

import pytest

from fief.tasks.cleanup import CleanupTask


@pytest.mark.asyncio
class TestTasksCleanup:
    async def test_cleanup(self, main_session_manager, send_task_mock: MagicMock):
        cleanup = CleanupTask(main_session_manager, send_task=send_task_mock)
        await cleanup.run()
