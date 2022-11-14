from typing import Generic

from fastapi import Depends

from fief.db import AsyncSession
from fief.dependencies.db import get_main_async_session
from fief.repositories import get_repository
from fief.repositories.base import REPOSITORY


class get_main_repository(Generic[REPOSITORY]):
    def __init__(self, repository_class: type[REPOSITORY]):
        self.repository_class = repository_class

    async def __call__(
        self, session: AsyncSession = Depends(get_main_async_session)
    ) -> REPOSITORY:
        return get_repository(self.repository_class, session)
