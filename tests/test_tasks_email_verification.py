from unittest.mock import MagicMock

import pytest

from fief.models import Workspace
from fief.services.email import EmailProvider
from fief.tasks.email_verification import OnEmailVerificationRequestedTask
from tests.data import TestData, email_verification_codes


@pytest.mark.asyncio
class TestTasksOnEmailVerificationRequestedTask:
    async def test_send_verify_email(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
    ):
        email_provider_mock = MagicMock(spec=EmailProvider)

        on_email_verification_requested = OnEmailVerificationRequestedTask(
            main_session_manager, workspace_session_manager, email_provider_mock
        )

        email_verification = test_data["email_verifications"]["not_verified_email"]
        await on_email_verification_requested.run(
            str(email_verification.id),
            str(workspace.id),
            email_verification_codes["not_verified_email"][0],
        )

        email_provider_mock.send_email.assert_called_once()
