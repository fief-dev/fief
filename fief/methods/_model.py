import typing

D = typing.TypeVar("D", bound=typing.Mapping[str, typing.Any])


class MethodModelProtocol(typing.Protocol[D]):
    id: typing.Any
    name: str
    user_id: typing.Any
    data: D


_all__ = [
    "MethodModelProtocol",
]
