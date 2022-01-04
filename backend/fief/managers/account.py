from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Account


class AccountManager(BaseManager[Account], UUIDManagerMixin[Account]):
    model = Account
