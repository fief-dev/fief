from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Tenant


class TenantManager(BaseManager[Tenant], UUIDManagerMixin[Tenant]):
    model = Tenant
