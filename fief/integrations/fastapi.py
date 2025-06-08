import typing

from fastapi import FastAPI, Request

from .._core import FiefAsync, FiefAsyncRequest, U
from .starlette import FiefMiddleware, MissingFiefRequestException


class FiefFastAPI(typing.Generic[U]):
    def __init__(self, fief: FiefAsync[U]) -> None:
        self.fief = fief

    def add_middleware(self, app: FastAPI) -> None:
        app.add_middleware(FiefMiddleware[U], fief=self.fief)

    async def __call__(self, request: Request) -> FiefAsyncRequest[U]:
        try:
            return request.state.fief
        except AttributeError as e:
            raise MissingFiefRequestException() from e
