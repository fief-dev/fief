import contextlib
from collections.abc import AsyncGenerator

import asgi_lifespan
import httpx
import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from fief import FiefAsync
from fief._core import FiefAsyncRequest
from fief.integrations.starlette import (
    FiefMiddleware,
    MissingFiefRequestException,
    get_fief,
)
from tests.fixtures import MockAsyncProvider, UserModel


@contextlib.asynccontextmanager
async def get_client(app: Starlette) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with asgi_lifespan.LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://testserver"
        ) as client:
            yield client


@pytest.fixture
def fief() -> FiefAsync[UserModel]:
    return FiefAsync(
        storage=MockAsyncProvider(models=[UserModel]),
        methods=(),
        user_model=UserModel,
    )


@pytest.mark.anyio
async def test_middleware(fief: FiefAsync[UserModel]) -> None:
    async def index(request: Request) -> PlainTextResponse:
        fief = request.state.fief
        assert isinstance(fief, FiefAsyncRequest)
        return PlainTextResponse("Hello, world!")

    app = Starlette(
        routes=[Route("/", index)],
        middleware=[
            Middleware(FiefMiddleware[UserModel], fief=fief),
        ],
    )

    async with get_client(app) as client:
        response = await client.get("/")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_get_client_missing(fief: FiefAsync[UserModel]) -> None:
    async def index(request: Request) -> PlainTextResponse:
        with pytest.raises(MissingFiefRequestException):
            get_fief(request)
        return PlainTextResponse("Hello, world!")

    app = Starlette(routes=[Route("/", index)])

    async with get_client(app) as client:
        response = await client.get("/")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_get_client_ok(fief: FiefAsync[UserModel]) -> None:
    async def index(request: Request) -> PlainTextResponse:
        fief = get_fief(request)
        assert isinstance(fief, FiefAsyncRequest)
        return PlainTextResponse("Hello, world!")

    app = Starlette(
        routes=[Route("/", index)],
        middleware=[
            Middleware(FiefMiddleware[UserModel], fief=fief),
        ],
    )

    async with get_client(app) as client:
        response = await client.get("/")
        assert response.status_code == 200
