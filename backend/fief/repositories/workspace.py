import random
import string

from slugify import slugify
from sqlalchemy import select

from fief.models import Workspace
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin
from fief.settings import settings


class WorkspaceRepository(BaseRepository[Workspace], UUIDRepositoryMixin[Workspace]):
    model = Workspace

    async def get_by_domain(self, domain: str) -> Workspace | None:
        statement = select(Workspace).where(Workspace.domain == domain)
        return await self.get_one_or_none(statement)

    async def get_main(self) -> Workspace | None:
        return await self.get_by_domain(settings.fief_domain)

    async def get_available_subdomain(self, name: str) -> str:
        slug = slugify(name)
        domain = f"{slug}.{settings.root_domain}"
        workspace = await self.get_by_domain(domain)

        if workspace is None:
            return domain

        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        return f"{slug}-{random_string}.{settings.root_domain}"
