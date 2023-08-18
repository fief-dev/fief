from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from fief import tasks


def schedule():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        tasks.cleanup.send,
        CronTrigger.from_crontab("0 0 * * *"),
    )
    scheduler.add_job(
        tasks.count_users.send,
        CronTrigger.from_crontab("0 0 * * *"),
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()
