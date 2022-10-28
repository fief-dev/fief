from fief.models import EmailTemplate
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class EmailTemplateRepository(
    BaseRepository[EmailTemplate], UUIDRepositoryMixin[EmailTemplate]
):
    model = EmailTemplate
