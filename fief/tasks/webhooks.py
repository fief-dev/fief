import uuid

import dramatiq
from dramatiq.middleware import CurrentMessage

from fief.repositories import WebhookLogRepository, WebhookRepository
from fief.services.webhooks.delivery import WebhookDelivery, WebhookDeliveryError
from fief.services.webhooks.models import WebhookEvent
from fief.settings import settings
from fief.tasks.base import TaskBase, TaskError


class DeliverWebhookTask(TaskBase):
    __name__ = "deliver_webhook"

    async def run(self, workspace_id: str, webhook_id: str, event: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        async with self.get_workspace_session(workspace) as session:
            webhook_repository = WebhookRepository(session)
            webhook = await webhook_repository.get_by_id(uuid.UUID(webhook_id))

            if webhook is None:
                raise TaskError(f"Webhook {webhook_id} doesn't exist.")

            message = CurrentMessage.get_current_message()
            retries = message.options.get("retries", 0)

            webhook_log_repository = WebhookLogRepository(session)
            webhook_delivery = WebhookDelivery(webhook_log_repository)
            parsed_event = WebhookEvent.parse_raw(event)
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
            for webhook in webhooks:
                self.send_task(
                    deliver_webhook,
                    workspace_id=workspace_id,
                    webhook_id=str(webhook.id),
                    event=event,
                )


trigger_webhooks = dramatiq.actor(TriggerWebhooksTask())
