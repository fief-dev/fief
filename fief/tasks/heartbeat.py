import dramatiq

from fief.logger import logger
from fief.services.posthog import get_server_id, get_server_properties, posthog
from fief.settings import settings
from fief.tasks.base import TaskBase


class HeartbeatTask(TaskBase):
    __name__ = "heartbeat"

    async def run(self):
        if not settings.telemetry_enabled:
            logger.debug("Telemetry is disabled")
            return

        async with self.get_main_session() as session:
            server_id = get_server_id()
            server_properties = await get_server_properties(session)
            posthog.group_identify("server", server_id, properties=server_properties)
            posthog.flush()
            logger.debug(
                "Heartbeat sent to Posthog",
                server_id=server_id,
                server_properties=server_properties,
            )


heartbeat = dramatiq.actor(HeartbeatTask())
