from fief.models import Role
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class RoleRepository(BaseRepository[Role], UUIDRepositoryMixin[Role]):
    model = Role
