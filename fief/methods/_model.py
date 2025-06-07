import typing

from sqlalchemy.orm import Mapped

D = typing.TypeVar("D", bound=typing.Mapping[str, typing.Any])


class MethodModelRawProtocol(typing.Protocol[D]):
    id: typing.Any
    name: str
    user_id: typing.Any
    data: D


class MethodModelSQLAlchemyProtocol(typing.Protocol[D]):
    id: Mapped[typing.Any]
    name: Mapped[str]
    user_id: Mapped[typing.Any]
    data: Mapped[D]


MM = typing.TypeVar(
    "MM",
    bound=MethodModelRawProtocol[typing.Any]
    | MethodModelSQLAlchemyProtocol[typing.Any],
)

_all__ = [
    "MethodModelRawProtocol",
    "MethodModelSQLAlchemyProtocol",
    "MM",
]
