from fief.tasks import SendTask, send_task


async def get_send_task() -> SendTask:
    return send_task
