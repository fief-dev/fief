import typing


class ProtocolModel(typing.Protocol):
    id: typing.Any
    type: str
    user_id: typing.Any
    data: dict[str, typing.Any]


_all__ = [
    "ProtocolModel",
]
