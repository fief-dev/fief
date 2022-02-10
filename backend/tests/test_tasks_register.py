from unittest.mock import MagicMock

import pytest

from fief.models import Account
from fief.services.email import EmailProvider
from fief.tasks.register import OnAfterRegisterTask
from tests.data import TestData


@pytest.mark.asyncio
class TestTasksOnAfterRegister:
    async def test_send_welcome_email(
        self,
        account: Account,
        global_session_manager,
        account_session_manager,
        test_data: TestData,
    ):
        email_provider_mock = MagicMock(spec=EmailProvider)

        on_after_register = OnAfterRegisterTask(
            global_session_manager, account_session_manager, email_provider_mock
        )

        user = test_data["users"]["regular"]
        await on_after_register.run(user.id, account.id)

        email_provider_mock.send_email.assert_called_once()
