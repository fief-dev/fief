import functools

from fastapi import Depends

from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.tasks import get_send_task
from fief.models import Workspace
from fief.services.webhooks.trigger import TriggerWebhooks, trigger_webhooks
from fief.tasks import SendTask


async def get_trigger_webhooks(
    workspace: Workspace = Depends(get_current_workspace),
    send_task: SendTask = Depends(get_send_task),
) -> TriggerWebhooks:
    return functools.partial(
        trigger_webhooks, workspace_id=workspace.id, send_task=send_task
    )
