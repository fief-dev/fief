import uuid

import dramatiq
from dramatiq.middleware import CurrentMessage

from fief.models import Webhook
from fief.repositories import WebhookLogRepository, WebhookRepository
from fief.services.webhooks.delivery import WebhookDelivery, WebhookDeliveryError
from fief.services.webhooks.models import WebhookEvent
from fief.settings import settings
from fief.tasks.base import ObjectDoesNotExistTaskError, TaskBase


class DeliverWebhookTask(TaskBase):
    __name__ = "deliver_webhook"

    async def run(self, workspace_id: str, webhook_id: str, event: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        async with self.get_workspace_session(workspace) as session:
            webhook_repository = WebhookRepository(session)
            webhook = await webhook_repository.get_by_id(uuid.UUID(webhook_id))

            if webhook is None:
                raise ObjectDoesNotExistTaskError(Webhook, webhook_id)

            message = CurrentMessage.get_current_message()
            retries = message.options.get("retries", 0)

            webhook_log_repository = WebhookLogRepository(session)
            webhook_delivery = WebhookDelivery(webhook_log_repository)
            parsed_event = WebhookEvent.model_validate_json(event)
            await webhook_delivery.deliver(webhook, parsed_event, attempt=retries + 1)


def should_retry_deliver_webhook(retries_so_far, exception):
    return retries_so_far < settings.webhooks_max_attempts and isinstance(
        exception, WebhookDeliveryError
    )


deliver_webhook = dramatiq.actor(
    DeliverWebhookTask(), retry_when=should_retry_deliver_webhook
)


class TriggerWebhooksTask(TaskBase):
    __name__ = "trigger_webhooks"

    async def run(self, workspace_id: str, event: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        async with self.get_workspace_session(workspace) as session:
            webhook_repository = WebhookRepository(session)
            webhooks = await webhook_repository.all()
            parsed_event = WebhookEvent.model_validate_json(event)
            for webhook in webhooks:
                if parsed_event.type in webhook.events:
                    self.send_task(
                        deliver_webhook,
                        workspace_id=workspace_id,
                        webhook_id=str(webhook.id),
                        event=event,
                    )


trigger_webhooks = dramatiq.actor(TriggerWebhooksTask())
