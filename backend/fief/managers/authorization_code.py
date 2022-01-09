from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import AuthorizationCode


class AuthorizationCodeManager(
    BaseManager[AuthorizationCode], UUIDManagerMixin[AuthorizationCode]
):
    model = AuthorizationCode
