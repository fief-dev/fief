from unittest.mock import MagicMock

import httpx
import pytest
import respx
from dramatiq import Message
from dramatiq.middleware import CurrentMessage
from pytest_mock import MockerFixture

from fief.models import Workspace
from fief.services.webhooks.delivery import WebhookDeliveryError
from fief.services.webhooks.models import (
    ClientCreated,
    UserCreated,
    UserRoleDeleted,
    WebhookEvent,
)
from fief.tasks.webhooks import DeliverWebhookTask, TriggerWebhooksTask
from tests.data import TestData


@pytest.fixture
def webhook_event() -> WebhookEvent:
    return WebhookEvent(type=ClientCreated.key(), data={})


@pytest.mark.asyncio
class TestTasksDeliverWebhook:
    async def test_deliver_success(
        self,
        mocker: MockerFixture,
        respx_mock: respx.MockRouter,
        webhook_event: WebhookEvent,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
    ):
        get_current_message_mock = mocker.patch.object(
            CurrentMessage, "get_current_message"
        )
        get_current_message_mock.return_value = Message("queue", "actor", (), {}, {})

        webhook = test_data["webhooks"]["all"]
        route_mock = respx_mock.post(webhook.url).mock(return_value=httpx.Response(200))

        deliver_webhook = DeliverWebhookTask(
            main_session_manager, workspace_session_manager
        )

        await deliver_webhook.run(
            str(workspace.id), str(webhook.id), webhook_event.json()
        )

        assert route_mock.called

    async def test_deliver_error(
        self,
        mocker: MockerFixture,
        respx_mock: respx.MockRouter,
        webhook_event: WebhookEvent,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
    ):
        get_current_message_mock = mocker.patch.object(
            CurrentMessage, "get_current_message"
        )
        get_current_message_mock.return_value = Message("queue", "actor", (), {}, {})

        webhook = test_data["webhooks"]["all"]
        respx_mock.post(webhook.url).mock(return_value=httpx.Response(400))

        deliver_webhook = DeliverWebhookTask(
            main_session_manager, workspace_session_manager
        )

        with pytest.raises(WebhookDeliveryError):
            await deliver_webhook.run(
                str(workspace.id), str(webhook.id), webhook_event.json()
            )


@pytest.mark.asyncio
class TestTasksTriggerWebhooks:
    async def test_client_created_event(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        webhook_event = WebhookEvent(type=ClientCreated.key(), data={})

        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == 1
        assert send_task_mock.call_args[1]["webhook_id"] == str(
            test_data["webhooks"]["all"].id
        )

    async def test_user_registered_event(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        webhook_event = WebhookEvent(type=UserCreated.key(), data={})

        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == 2
        webhook_ids = [
            call_arg[1]["webhook_id"] for call_arg in send_task_mock.call_args_list
        ]
        assert str(test_data["webhooks"]["all"].id) in webhook_ids
        assert str(test_data["webhooks"]["user_created"].id) in webhook_ids

    async def test_user_role_deleted_event(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        webhook_event = WebhookEvent(type=UserRoleDeleted.key(), data={})

        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == 2
        webhook_ids = [
            call_arg[1]["webhook_id"] for call_arg in send_task_mock.call_args_list
        ]
        assert str(test_data["webhooks"]["all"].id) in webhook_ids
        assert str(test_data["webhooks"]["object_user_role"].id) in webhook_ids
