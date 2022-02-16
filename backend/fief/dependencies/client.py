from typing import List, Tuple

from fastapi import Depends
from sqlalchemy import select

from fief.dependencies.account_managers import get_client_manager
from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.managers import ClientManager
from fief.models import Client


async def get_paginated_clients(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: ClientManager = Depends(get_client_manager),
) -> Tuple[List[Client], int]:
    statement = select(Client)
    return await get_paginated_objects(statement, pagination, ordering, manager)
