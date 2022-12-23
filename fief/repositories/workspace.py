import random
import string
import uuid

from slugify import slugify
from sqlalchemy import select

from fief.models import Workspace, WorkspaceUser
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin
from fief.settings import settings


class WorkspaceRepository(BaseRepository[Workspace], UUIDRepositoryMixin[Workspace]):
    model = Workspace

    async def get_by_admin_user(self, user_id: uuid.UUID) -> list[Workspace]:
        statement = (
            select(Workspace)
            .join(Workspace.workspace_users)
            .where(WorkspaceUser.user_id == user_id)
        )
        return await self.list(statement)

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
