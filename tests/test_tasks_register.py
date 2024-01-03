from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from fief.db import AsyncSession
from fief.repositories import UserRoleRepository
from fief.services.email import EmailProvider
from fief.tasks.register import OnAfterRegisterTask
from fief.tasks.user_permissions import on_user_role_created
from tests.data import TestData


@pytest.fixture(autouse=True)
def mock_send_task(mocker: MockerFixture, send_task_mock: MagicMock):
    mocker.patch("fief.tasks.register.send_task", new=send_task_mock)


@pytest.mark.asyncio
class TestTasksOnAfterRegister:
    async def test_send_welcome_email(self, main_session_manager, test_data: TestData):
        email_provider_mock = MagicMock(spec=EmailProvider)

        on_after_register = OnAfterRegisterTask(
            main_session_manager, email_provider_mock
        )

        user = test_data["users"]["regular"]
        await on_after_register.run(str(user.id))

        email_provider_mock.send_email.assert_called_once()

    async def test_default_roles_granted(
        self,
        main_session_manager,
        main_session: AsyncSession,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        email_provider_mock = MagicMock(spec=EmailProvider)

        on_after_register = OnAfterRegisterTask(
            main_session_manager, email_provider_mock
        )

        user = test_data["users"]["regular_secondary"]
        await on_after_register.run(str(user.id))

        user_role_repository = UserRoleRepository(main_session)
        user_roles = await user_role_repository.list(
            user_role_repository.get_by_user_statement(user.id)
        )
        assert len(user_roles) == 1

        for user_role in user_roles:
            send_task_mock.assert_called_with(
                on_user_role_created, str(user.id), str(user_role.role_id)
            )
