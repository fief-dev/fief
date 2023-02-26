from unittest.mock import MagicMock

import pytest
import respx
import httpx
from dramatiq.middleware import CurrentMessage
from pytest_mock import MockerFixture

from fief.models import Workspace
from fief.tasks.webhooks import DeliverWebhookTask, TriggerWebhooksTask
from tests.data import TestData
from fief import schemas
from fief.services.webhooks.models import WebhookEvent, WebhookEventType
from fief.services.webhooks.delivery import WebhookDeliveryError


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

        webhook = test_data["webhooks"]["default"]
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

        webhook = test_data["webhooks"]["default"]
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
    async def test_success(
        self,
        webhook_event: WebhookEvent,
        workspace: Workspace,
        main_session_manager,
        workspace_session_manager,
        test_data: TestData,
        send_task_mock: MagicMock,
    ):
        trigger_webhooks = TriggerWebhooksTask(
            main_session_manager, workspace_session_manager, send_task=send_task_mock
        )

        await trigger_webhooks.run(str(workspace.id), webhook_event.json())

        assert send_task_mock.call_count == len(test_data["webhooks"])
