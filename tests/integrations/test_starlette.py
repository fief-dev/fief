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
    FiefStarlette,
    MissingFiefRequestException,
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


@pytest.fixture
def fief_starlette(fief: FiefAsync[UserModel]) -> FiefStarlette[UserModel]:
    return FiefStarlette(fief)


@pytest.mark.anyio
class TestFiefStarlette:
    async def test_get_middleware_missing(
        self, fief_starlette: FiefStarlette[UserModel]
    ) -> None:
        async def index(request: Request) -> PlainTextResponse:
            with pytest.raises(MissingFiefRequestException):
                fief_starlette.get(request)
            return PlainTextResponse("Hello, world!")

        app = Starlette(routes=[Route("/", index)])

        async with get_client(app) as client:
            await client.get("/")

    async def test_get_ok(self, fief_starlette: FiefStarlette[UserModel]) -> None:
        async def index(request: Request) -> PlainTextResponse:
            fief = fief_starlette.get(request)
            assert isinstance(fief, FiefAsyncRequest)
            return PlainTextResponse("Hello, world!")

        app = Starlette(
            routes=[Route("/", index)],
            middleware=[fief_starlette.get_middleware()],
        )

        async with get_client(app) as client:
            response = await client.get("/")
            assert response.status_code == 200
