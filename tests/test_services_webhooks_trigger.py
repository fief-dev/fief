from unittest.mock import MagicMock

from fief import schemas
from fief.services.webhooks.models import ClientCreated, WebhookEvent
from fief.services.webhooks.trigger import trigger_webhooks
from tests.data import TestData


def test_trigger_webhooks(test_data: TestData, send_task_mock: MagicMock):
    object = test_data["clients"]["default_tenant"]

    trigger_webhooks(
        ClientCreated, object, schemas.client.Client, send_task=send_task_mock
    )

    send_task_mock.assert_called_once()

    event_json = send_task_mock.call_args[1]["event"]
    event = WebhookEvent.model_validate_json(event_json)
    assert event.type == ClientCreated.key()
    assert event.data["id"] == str(object.id)
