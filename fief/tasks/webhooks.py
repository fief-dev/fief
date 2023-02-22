import uuid

import dramatiq
from dramatiq.middleware import CurrentMessage

from fief.repositories import WebhookLogRepository, WebhookRepository
from fief.services.webhooks import WebhookDelivery, WebhookDeliveryError
from fief.tasks.base import TaskBase, TaskError
from fief.settings import settings


class SendWebhookTask(TaskBase):
    __name__ = "send_webhook"

    async def run(self, workspace_id: str, webhook_id: str, event):
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
            await webhook_delivery.send(webhook, event, attempt=retries + 1)


def should_retry_send_webhook(retries_so_far, exception):
    return retries_so_far < settings.webhooks_max_attempts and isinstance(
        exception, WebhookDeliveryError
    )


send_webhook = dramatiq.actor(SendWebhookTask(), retry_when=should_retry_send_webhook)
