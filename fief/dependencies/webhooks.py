import functools

from fastapi import Depends

from fief.dependencies.tasks import get_send_task
from fief.services.webhooks.trigger import TriggerWebhooks, trigger_webhooks
from fief.tasks import SendTask


async def get_trigger_webhooks(
    send_task: SendTask = Depends(get_send_task),
) -> TriggerWebhooks:
    return functools.partial(trigger_webhooks, send_task=send_task)
