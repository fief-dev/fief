import asyncio
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

from pydantic import UUID4
from sqlalchemy import func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import Select

from fief.models.generics import M_UUID, M


class BaseManagerProtocol(Protocol[M]):
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

    async def _execute_statement(self, statement: Select) -> Result:
        ...  # pragma: no cover


class UUIDManagerProtocol(BaseManagerProtocol, Protocol[M_UUID]):
    model: Type[M_UUID]

    async def get_by_id(self, id: UUID4) -> Optional[M_UUID]:
        ...  # pragma: no cover


class BaseManager(BaseManagerProtocol, Generic[M]):
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
            self._count(statement), self._execute_statement(paginated_statement)
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

    async def get_one_or_none(self, statement: Select) -> Optional[M]:
        results = await self._execute_statement(statement)
        object = results.first()
        if object is None:
            return None
        return object[0]

    async def list(self, statement: Select) -> List[M]:
        results = await self._execute_statement(statement)
        return [result[0] for result in results.unique().all()]

    async def create(self, object: M) -> M:
        self.session.add(object)
        await self.session.commit()
        await self.session.refresh(object)
        return object

    async def create_many(self, objects: List[M]) -> List[M]:
        for object in objects:
            self.session.add(object)
        await self.session.commit()
        return objects

    async def update(self, object: M) -> None:
        self.session.add(object)
        await self.session.commit()
        await self.session.refresh(object)

    async def delete(self, object: M) -> None:
        await self.session.delete(object)
        await self.session.commit()

    async def _count(self, statement: Select) -> int:
        count_statement = statement.with_only_columns(
            [func.count()], maintain_column_froms=True  # type: ignore
        ).order_by(None)
        results = await self._execute_statement(count_statement)
        return results.scalar_one()

    async def _execute_statement(self, statement: Select) -> Result:
        return await self.session.execute(statement)


class UUIDManagerMixin(Generic[M_UUID]):
    async def get_by_id(
        self: UUIDManagerProtocol[M_UUID],
        id: UUID4,
        options: Optional[Sequence[Any]] = None,
    ) -> Optional[M_UUID]:
        statement = select(self.model).where(self.model.id == id)

        if options is not None:
            statement = statement.options(*options)

        return await self.get_one_or_none(statement)


MANAGER = TypeVar("MANAGER", bound=BaseManager)


def get_manager(manager_class: Type[MANAGER], session: AsyncSession) -> MANAGER:
    return manager_class(session)
