from fief.models import AuditLog
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class AuditLogRepository(BaseRepository[AuditLog], UUIDRepositoryMixin[AuditLog]):
    model = AuditLog
