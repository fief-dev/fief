import typing

T = typing.TypeVar("T", bound=str)
D = typing.TypeVar("D", bound=typing.Mapping[str, typing.Any])


class ProtocolModel(typing.Protocol[T, D]):
    id: typing.Any
    type: T
    user_id: typing.Any
    data: D


_all__ = [
    "ProtocolModel",
]
