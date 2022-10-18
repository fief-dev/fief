from typing import Generic, Type

from fastapi import Depends

from fief.db import AsyncSession
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.repositories import get_repository
from fief.repositories.base import REPOSITORY


class get_workspace_repository(Generic[REPOSITORY]):
    def __init__(self, repository_class: Type[REPOSITORY]):
        self.repository_class = repository_class

    async def __call__(
        self, session: AsyncSession = Depends(get_current_workspace_session)
    ) -> REPOSITORY:
        return get_repository(self.repository_class, session)
