from unittest.mock import MagicMock

import httpx
import pytest
import respx
from dramatiq.middleware import CurrentMessage
from pytest_mock import MockerFixture

from fief import schemas
from fief.models import Workspace
from fief.services.webhooks.delivery import WebhookDeliveryError
from fief.services.webhooks.models import WebhookEvent, WebhookEventType
from fief.tasks.webhooks import DeliverWebhookTask, TriggerWebhooksTask
from tests.data import TestData


@pytest.fixture
def webhook_event(test_data: TestData) -> WebhookEvent:
    object = test_data["clients"]["default_tenant"]
    return WebhookEvent(
        type=WebhookEventType.OBJECT_CREATED,
        object=type(object).__name__,
        data=schemas.client.Client.from_orm(object).dict(),
    )


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
        mocker.patch.object(CurrentMessage, "get_current_message")

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
        mocker.patch.object(CurrentMessage, "get_current_message")

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
        object = test_data["clients"]["default_tenant"]
        webhook_event = WebhookEvent(
            type=WebhookEventType.OBJECT_CREATED,
            object=type(object).__name__,
            data=schemas.client.Client.from_orm(object).dict(),
        )

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
        object = test_data["users"]["regular"]
        webhook_event = WebhookEvent(
            type=WebhookEventType.USER_REGISTERED,
            object=type(object).__name__,
            data=schemas.user.UserRead.from_orm(object).dict(),
        )

        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == 2
        assert send_task_mock.call_args_list[0][1]["webhook_id"] == str(
            test_data["webhooks"]["all"].id
        )
        assert send_task_mock.call_args_list[1][1]["webhook_id"] == str(
            test_data["webhooks"]["user_registered"].id
        )

    async def test_user_role_deleted_event(
        self,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        object = test_data["user_roles"]["default_castles_visitor"]
        webhook_event = WebhookEvent(
            type=WebhookEventType.OBJECT_DELETED,
            object=type(object).__name__,
            data=schemas.user_role.UserRole.from_orm(object).dict(),
        )

        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == 2
        assert send_task_mock.call_args_list[0][1]["webhook_id"] == str(
            test_data["webhooks"]["all"].id
        )
        assert send_task_mock.call_args_list[1][1]["webhook_id"] == str(
            test_data["webhooks"]["object_user_role"].id
        )
