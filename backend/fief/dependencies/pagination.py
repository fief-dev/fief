from typing import List, Tuple

from fastapi import Query
from sqlalchemy.sql import Select

from fief.repositories.base import BaseRepository, M

PaginatedObjects = Tuple[List[M], int]


async def get_paginated_objects(
    statement: Select,
    pagination: Tuple[int, int],
    ordering: List[Tuple[List[str], bool]],
    repository: BaseRepository[M],
) -> PaginatedObjects[M]:
    limit, skip = pagination
    statement = repository.orderize(statement, ordering)
    return await repository.paginate(statement, limit, skip)


Pagination = Tuple[int, int]


async def get_pagination(
    limit: int = Query(10, gt=0), skip: int = Query(0)
) -> Pagination:
    return min(limit, 100), skip


Ordering = List[Tuple[List[str], bool]]


async def get_ordering(ordering: str = Query(None)) -> Ordering:
    ordering_fields = []
    if ordering:
        fields = ordering.split(",")
        for field in fields:
            is_desc = False
            if field.startswith("-"):
                is_desc = True
                field = field[1:]
            ordering_fields.append((field.split("."), is_desc))
    return ordering_fields
