from typing import Protocol

from pydantic import UUID4

from fief.models import M
from fief.schemas.generics import PM
from fief.services.webhooks.models import WebhookEvent, WebhookEventType
from fief.tasks import SendTask
from fief.tasks import trigger_webhooks as trigger_webhooks_task


def trigger_webhooks(
    event_type: type[WebhookEventType],
    object: M,
    schema_class: type[PM],
    *,
    workspace_id: UUID4,
    send_task: SendTask,
) -> None:
    event: WebhookEvent = WebhookEvent(
        type=event_type.key(), data=schema_class.from_orm(object).dict()
    )
    send_task(trigger_webhooks_task, workspace_id=str(workspace_id), event=event.json())


class TriggerWebhooks(Protocol):
    def __call__(
        self, event_type: type[WebhookEventType], object: M, schema_class: type[PM]
    ) -> None:
        ...
