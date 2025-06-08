import contextlib
from collections.abc import AsyncGenerator

import asgi_lifespan
import exceptiongroup
import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse

from fief import FiefAsync
from fief._core import FiefAsyncRequest
from fief.integrations.fastapi import FiefFastAPI
from fief.integrations.starlette import MissingFiefRequestException
from tests.fixtures import MockAsyncProvider, UserModel


@contextlib.asynccontextmanager
async def get_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
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


@pytest.fixture
def fief_fastapi(fief: FiefAsync[UserModel]) -> FiefFastAPI[UserModel]:
    return FiefFastAPI(fief)


@pytest.mark.anyio
class TestFiefFastAPI:
    async def test_call_middleware_missing(
        self, fief_fastapi: FiefFastAPI[UserModel]
    ) -> None:
        app = FastAPI()

        @app.get("/")
        async def index(
            fief_request: FiefAsyncRequest[UserModel] = Depends(fief_fastapi),
        ) -> PlainTextResponse:
            return PlainTextResponse("Hello, world!")

        with pytest.raises(
            (MissingFiefRequestException, exceptiongroup.ExceptionGroup)
        ) as e:
            async with get_client(app) as client:
                await client.get("/")

        if isinstance(e.value, exceptiongroup.ExceptionGroup):
            assert len(e.value.exceptions) == 1
            assert isinstance(e.value.exceptions[0], MissingFiefRequestException)

    async def test_call_ok(self, fief_fastapi: FiefFastAPI[UserModel]) -> None:
        app = FastAPI()
        fief_fastapi.add_middleware(app)

        @app.get("/")
        async def index(
            fief_request: FiefAsyncRequest[UserModel] = Depends(fief_fastapi),
        ) -> PlainTextResponse:
            assert isinstance(fief_request, FiefAsyncRequest)
            return PlainTextResponse("Hello, world!")

        async with get_client(app) as client:
            response = await client.get("/")
            assert response.status_code == 200
