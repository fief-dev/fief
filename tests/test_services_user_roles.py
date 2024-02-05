from unittest.mock import MagicMock

import pytest

from fief.db import AsyncSession
from fief.logger import AuditLogger, logger
from fief.repositories import (
    RoleRepository,
    UserPermissionRepository,
    UserRoleRepository,
)
from fief.services.user_roles import UserRolesService
from tests.data import TestData


@pytest.fixture
def trigger_webhooks_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def user_roles_service(
    main_session: AsyncSession,
    trigger_webhooks_mock: MagicMock,
    send_task_mock: MagicMock,
) -> UserRolesService:
    return UserRolesService(
        UserRoleRepository(main_session),
        UserPermissionRepository(main_session),
        RoleRepository(main_session),
        AuditLogger(logger),
        trigger_webhooks_mock,
        send_task_mock,
    )


@pytest.mark.asyncio
async def test_add_default_roles(
    main_session: AsyncSession,
    test_data: TestData,
    user_roles_service: UserRolesService,
) -> None:
    user = test_data["users"]["regular_secondary"]

    await user_roles_service.add_default_roles(user, run_in_worker=False)

    user_role_repository = UserRoleRepository(main_session)
    user_roles = await user_role_repository.list(
        user_role_repository.get_by_user_statement(user.id)
    )
    assert len(user_roles) == 1

    user_permission_repository = UserPermissionRepository(main_session)
    user_permissions = await user_permission_repository.list(
        user_permission_repository.get_by_user_statement(user.id)
    )
    assert len(user_permissions) == 1
