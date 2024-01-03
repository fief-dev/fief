import uuid

import pytest

from fief.db import AsyncSession
from fief.repositories import UserPermissionRepository
from fief.tasks.base import TaskError
from fief.tasks.roles import OnRoleUpdated
from tests.data import TestData


@pytest.mark.asyncio
class TestTasksOnRoleUpdated:
    async def test_not_existing_role(
        self,
        main_session_manager,
        not_existing_uuid: uuid.UUID,
    ):
        on_user_role_updated = OnRoleUpdated(main_session_manager)

        with pytest.raises(TaskError):
            await on_user_role_updated.run(str(not_existing_uuid), [], [])

    async def test_role_created_added_permission(
        self,
        main_session_manager,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        on_user_role_updated = OnRoleUpdated(main_session_manager)

        role = test_data["roles"]["castles_visitor"]
        permission = test_data["permissions"]["castles:create"]
        await on_user_role_updated.run(str(role.id), [str(permission.id)], [])

        user = test_data["users"]["regular"]
        user_permission_repository = UserPermissionRepository(main_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id)
        )
        assert len(user_permissions) == 3
        assert permission.id in [
            user_permission.permission_id for user_permission in user_permissions
        ]

    async def test_role_created_deleted_permission(
        self,
        main_session_manager,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        on_user_role_updated = OnRoleUpdated(main_session_manager)

        role = test_data["roles"]["castles_visitor"]
        permission = test_data["permissions"]["castles:read"]
        await on_user_role_updated.run(str(role.id), [], [str(permission.id)])

        user = test_data["users"]["regular"]
        user_permission_repository = UserPermissionRepository(main_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id)
        )
        assert len(user_permissions) == 1
        assert permission.id not in [
            user_permission.permission_id for user_permission in user_permissions
        ]
