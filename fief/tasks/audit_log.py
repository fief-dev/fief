import json
from datetime import datetime
from typing import Any

import dramatiq

from fief.models import AuditLog
from fief.repositories import AuditLogRepository
from fief.tasks.base import TaskBase


class WriteAuditLog(TaskBase):
    __name__ = "write_audit_log"

    async def run(self, record: str):
        parsed_record: dict[str, Any] = json.loads(record)
        extra = parsed_record["extra"]

        async with self.get_main_session() as session:
            audit_log_repository = AuditLogRepository(session)
            extra.pop("audit")
            subject_user_id = extra.pop("subject_user_id", None)
            object_id = extra.pop("object_id", None)
            object_class = extra.pop("object_class", None)
            admin_user_id = extra.pop("admin_user_id", None)
            admin_api_key_id = extra.pop("admin_api_key_id", None)
            audit_log = AuditLog(
                timestamp=datetime.fromisoformat(parsed_record["time"]),
                level=parsed_record["level"],
                message=parsed_record["message"],
                subject_user_id=subject_user_id,
                object_id=object_id,
                object_class=object_class,
                admin_user_id=admin_user_id,
                admin_api_key_id=admin_api_key_id,
                extra=extra,
            )
            await audit_log_repository.create(audit_log)


write_audit_log = dramatiq.actor(WriteAuditLog())
