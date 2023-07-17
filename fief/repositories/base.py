from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Generic, Protocol, TypeVar, cast

from pydantic import UUID4
from sqlalchemy import delete, func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty, contains_eager
from sqlalchemy.sql import Executable, Select

from fief.models.generics import M_EXPIRES_AT, M_UUID, M


class BaseRepositoryProtocol(Protocol[M]):
    model: type[M]
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        ...

    async def paginate(
        self,
        statement: Select,
        limit=10,
        skip=0,
    ) -> tuple[list[M], int]:
        ...  # pragma: no cover

    def orderize(
        self, statement: Select, ordering: list[tuple[list[str], bool]]
    ) -> Select:
        ...  # pragma: no cover

    async def get_one_or_none(self, statement: Select) -> M | None:
        ...  # pragma: no cover

    async def list(self, statement: Select) -> list[M]:
        ...  # pragma: no cover

    async def create(self, object: M) -> M:
        ...  # pragma: no cover

    async def update(self, object: M) -> None:
        ...  # pragma: no cover

    async def delete(self, object: M) -> None:
        ...  # pragma: no cover

    async def _execute_query(self, statement: Select) -> Result:
        ...  # pragma: no cover

    async def _execute_statement(self, statement: Executable) -> Result:
        ...  # pragma: no cover


class UUIDRepositoryProtocol(BaseRepositoryProtocol, Protocol[M_UUID]):
    model: type[M_UUID]

    async def get_by_id(self, id: UUID4) -> M_UUID | None:
        ...  # pragma: no cover


class ExpiresAtRepositoryProtocol(BaseRepositoryProtocol, Protocol[M_EXPIRES_AT]):
    model: type[M_EXPIRES_AT]

    async def delete_expired(self) -> None:
        ...  # pragma: no cover


class BaseRepository(BaseRepositoryProtocol, Generic[M]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def paginate(
        self,
        statement: Select,
        limit=10,
        skip=0,
    ) -> tuple[list[M], int]:
        paginated_statement = statement.offset(skip).limit(limit)
        # FIXME: running it concurrently causes issues with SQLite and SQLAlchemy2
        count = await self._count(statement)
        results = await self.list(paginated_statement)
        return results, count

    def orderize(
        self, statement: Select, ordering: list[tuple[list[str], bool]]
    ) -> Select:
        for accessors, is_desc in ordering:
            field: InstrumentedAttribute
            # Local field
            if len(accessors) == 1:
                try:
                    field = getattr(self.model, accessors[0])
                    if not isinstance(
                        field.prop, RelationshipProperty
                    ):  # Prevent ordering by raw relation ship field -> "tenant" instead of "tenant.id"
                        statement = statement.order_by(
                            field.desc() if is_desc else field.asc()
                        )
                except AttributeError:
                    pass
            # Relationship field
            else:
                valid_field = True
                model = self.model
                for accessor in accessors:
                    try:
                        field = getattr(model, accessor)
                        if isinstance(field.prop, RelationshipProperty):
                            statement = statement.join(field)
                            if field.prop.lazy == "joined":
                                # If the relationship is eagerly loaded,
                                # this ensures we reuse the existing JOIN instead of adding another
                                # Ref: https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#routing-explicit-joins-statements-into-eagerly-loaded-collections
                                statement = statement.options(contains_eager(field))
                            model = field.prop.entity.class_
                    except AttributeError:
                        valid_field = False
                        break
                if valid_field:
                    statement = statement.order_by(
                        field.desc() if is_desc else field.asc()
                    )
        return statement

    async def all(self) -> list[M]:
        return await self.list(select(self.model))

    async def get_one_or_none(self, statement: Select) -> M | None:
        result = await self._execute_query(statement)
        return result.scalar()

    async def create(self, object: M) -> M:
        self.session.add(object)
        await self.session.commit()
        return object

    async def update(self, object: M) -> None:
        self.session.add(object)
        await self.session.commit()

    async def delete(self, object: M) -> None:
        await self.session.delete(object)
        await self.session.commit()

    async def create_many(self, objects: list[M]) -> list[M]:
        self.session.add_all(objects)
        await self.session.commit()
        return objects

    async def list(self, statement: Select) -> list[M]:
        result = await self._execute_query(statement)
        return cast(list[M], result.scalars().unique().all())

    async def _count(self, statement: Select) -> int:
        count_statement = statement.with_only_columns(
            func.count(), maintain_column_froms=True
        ).order_by(None)
        result = await self._execute_query(count_statement)
        return result.scalar_one()

    async def _execute_query(self, statement: Select) -> Result:
        return await self.session.execute(statement)

    async def _execute_statement(self, statement: Executable) -> Result:
        result = await self.session.execute(statement)
        await self.session.commit()
        return result


class UUIDRepositoryMixin(Generic[M_UUID]):
    async def get_by_id(
        self: UUIDRepositoryProtocol[M_UUID],
        id: UUID4,
        options: Sequence[Any] | None = None,
    ) -> M_UUID | None:
        statement = select(self.model).where(self.model.id == id)

        if options is not None:
            statement = statement.options(*options)

        return await self.get_one_or_none(statement)


class ExpiresAtMixin(Generic[M_EXPIRES_AT]):
    async def delete_expired(self: ExpiresAtRepositoryProtocol[M_EXPIRES_AT]):
        statement = delete(self.model).where(self.model.expires_at < datetime.now(UTC))
        await self._execute_statement(statement)


REPOSITORY = TypeVar("REPOSITORY", bound=BaseRepository)


def get_repository(
    repository_class: type[REPOSITORY], session: AsyncSession
) -> REPOSITORY:
    return repository_class(session)
