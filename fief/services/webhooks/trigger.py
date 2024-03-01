from typing import Protocol

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
    send_task: SendTask,
) -> None:
    event: WebhookEvent = WebhookEvent(
        type=event_type.key(),
        data=schema_class.model_validate(object).model_dump(mode="json"),
    )
    send_task(
        trigger_webhooks_task,
        event=event.model_dump_json(),
    )


class TriggerWebhooks(Protocol):
    def __call__(
        self, event_type: type[WebhookEventType], object: M, schema_class: type[PM]
    ) -> None: ...
