from fastapi import Query, Depends
from sqlalchemy.sql import Select

from fief.repositories.base import BaseRepository, M

PaginatedObjects = tuple[list[M], int]


async def get_paginated_objects(
    statement: Select,
    pagination: tuple[int, int],
    ordering: list[tuple[list[str], bool]],
    repository: BaseRepository[M],
) -> PaginatedObjects[M]:
    limit, skip = pagination
    statement = repository.orderize(statement, ordering)
    return await repository.paginate(statement, limit, skip)


Pagination = tuple[int, int]


async def get_pagination(
    limit: int = Query(10, gt=0), skip: int = Query(0, ge=0)
) -> Pagination:
    return min(limit, 100), skip


RawOrdering = list[str]


async def get_raw_ordering(ordering: str = Query(None)) -> RawOrdering:
    return ordering.split(",") if ordering else []


Ordering = list[tuple[list[str], bool]]


async def get_ordering(
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
) -> Ordering:
    ordering_fields = []
    for field in raw_ordering:
        is_desc = False
        if field.startswith("-"):
            is_desc = True
            field = field[1:]
        ordering_fields.append((field.split("."), is_desc))
    return ordering_fields
