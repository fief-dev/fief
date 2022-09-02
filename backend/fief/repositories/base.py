import asyncio
from datetime import datetime, timezone
from typing import (
    Any,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from pydantic import UUID4
from sqlalchemy import delete, func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import Executable, Select

from fief.models.generics import M_EXPIRES_AT, M_UUID, M


class BaseRepositoryProtocol(Protocol[M]):
    model: Type[M]
    session: AsyncSession

    async def paginate(
        self,
        statement: Select,
        limit=10,
        skip=0,
    ) -> Tuple[List[M], int]:
        ...  # pragma: no cover

    def orderize(
        self, statement: Select, ordering: List[Tuple[List[str], bool]]
    ) -> Select:
        ...  # pragma: no cover

    async def get_one_or_none(self, statement: Select) -> Optional[M]:
        ...  # pragma: no cover

    async def list(self, statement: Select) -> List[M]:
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
    model: Type[M_UUID]

    async def get_by_id(self, id: UUID4) -> Optional[M_UUID]:
        ...  # pragma: no cover


class ExpiresAtRepositoryProtocol(BaseRepositoryProtocol, Protocol[M_EXPIRES_AT]):
    model: Type[M_EXPIRES_AT]

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
    ) -> Tuple[List[M], int]:
        paginated_statement = statement.offset(skip).limit(limit)
        [count, results] = await asyncio.gather(
            self._count(statement), self._execute_query(paginated_statement)
        )

        return [result[0] for result in results.unique().all()], count

    def orderize(
        self, statement: Select, ordering: List[Tuple[List[str], bool]]
    ) -> Select:
        for (accessors, is_desc) in ordering:
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
                            if field.prop.lazy != "joined":
                                statement = statement.join(field)
                            model = field.prop.entity.class_
                    except AttributeError:
                        valid_field = False
                        break
                if valid_field:
                    statement = statement.order_by(
                        field.desc() if is_desc else field.asc()
                    )
        return statement

    async def all(self) -> List[M]:
        return await self.list(select(self.model))

    async def get_one_or_none(self, statement: Select) -> Optional[M]:
        results = await self._execute_query(statement)
        object = results.first()
        if object is None:
            return None
        return object[0]

    async def list(self, statement: Select) -> List[M]:
        results = await self._execute_query(statement)
        return [result[0] for result in results.unique().all()]

    async def create(self, object: M) -> M:
        self.session.add(object)
        await self.session.commit()
        await self.session.refresh(object)
        return object

    async def update(self, object: M) -> None:
        self.session.add(object)
        await self.session.commit()
        await self.session.refresh(object)

    async def delete(self, object: M) -> None:
        await self.session.delete(object)
        await self.session.commit()

    async def create_many(self, objects: List[M]) -> List[M]:
        for object in objects:
            self.session.add(object)
        await self.session.commit()
        return objects

    async def _count(self, statement: Select) -> int:
        count_statement = statement.with_only_columns(
            [func.count()], maintain_column_froms=True  # type: ignore
        ).order_by(None)
        results = await self._execute_query(count_statement)
        return results.scalar_one()

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
        options: Optional[Sequence[Any]] = None,
    ) -> Optional[M_UUID]:
        statement = select(self.model).where(self.model.id == id)

        if options is not None:
            statement = statement.options(*options)

        return await self.get_one_or_none(statement)


class ExpiresAtMixin(Generic[M_EXPIRES_AT]):
    async def delete_expired(self: ExpiresAtRepositoryProtocol[M_EXPIRES_AT]):
        statement = delete(self.model).where(
            self.model.expires_at < datetime.now(timezone.utc)
        )
        await self.session.execute(statement)


REPOSITORY = TypeVar("REPOSITORY", bound=BaseRepository)


def get_repository(
    repository_class: Type[REPOSITORY], session: AsyncSession
) -> REPOSITORY:
    return repository_class(session)
