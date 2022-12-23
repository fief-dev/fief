import random
import string

from slugify import slugify
from sqlalchemy import select

from fief.models import Tenant
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class TenantRepository(BaseRepository[Tenant], UUIDRepositoryMixin[Tenant]):
    model = Tenant

    async def get_default(self) -> Tenant | None:
        statement = select(Tenant).where(Tenant.default == True)
        return await self.get_one_or_none(statement)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        statement = select(Tenant).where(Tenant.slug == slug)
        return await self.get_one_or_none(statement)

    async def get_available_slug(self, name: str) -> str:
        slug = slugify(name)
        tenant = await self.get_by_slug(slug)

        if tenant is None:
            return slug

        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        return f"{slug}-{random_string}"
