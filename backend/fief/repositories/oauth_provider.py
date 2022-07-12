from fief.models import OAuthProvider
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class OAuthProviderRepository(
    BaseRepository[OAuthProvider], UUIDRepositoryMixin[OAuthProvider]
):
    model = OAuthProvider
