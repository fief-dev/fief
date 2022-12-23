import uuid

import pytest

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import UserPermissionRepository
from fief.tasks.base import TaskError
from fief.tasks.user_permissions import OnUserRoleCreated, OnUserRoleDeleted
from tests.data import TestData


@pytest.mark.asyncio
class TestTasksOnUserRoleCreated:
    async def test_not_existing_role(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        on_user_role_created = OnUserRoleCreated(
            main_session_manager, workspace_session_manager
        )

        user = test_data["users"]["regular_secondary"]
        with pytest.raises(TaskError):
            await on_user_role_created.run(
                str(user.id), str(not_existing_uuid), str(workspace.id)
            )

    async def test_user_role_created(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        on_user_role_created = OnUserRoleCreated(
            main_session_manager, workspace_session_manager
        )

        user = test_data["users"]["regular_secondary"]
        role = test_data["roles"]["castles_manager"]
        await on_user_role_created.run(str(user.id), str(role.id), str(workspace.id))

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id)
        )
        assert len(user_permissions) == len(role.permissions)
        user_permissions_ids = [
            user_permission.permission_id for user_permission in user_permissions
        ]
        for permission in role.permissions:
            assert permission.id in user_permissions_ids


@pytest.mark.asyncio
class TestTasksOnUserRoleDeleted:
    async def test_user_role_deleted(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        on_user_role_deleted = OnUserRoleDeleted(
            main_session_manager, workspace_session_manager
        )

        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_visitor"]
        await on_user_role_deleted.run(str(user.id), str(role.id), str(workspace.id))

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id)
        )
        assert len(user_permissions) == 1
