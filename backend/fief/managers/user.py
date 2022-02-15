from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import User


class UserManager(BaseManager[User], UUIDManagerMixin[User]):
    model = User
