import pytest

from fief.dependencies.login_hint import LoginHint, get_login_hint
from tests.data import TestData


@pytest.mark.parametrize(
    "input,output",
    [
        (None, None),
        ("INVALID_VALUE", None),
        ("anne@bretagne.duchy", "anne@bretagne.duchy"),
        ("anne%40bretagne.duchy", "anne@bretagne.duchy"),
        ("b0133c88-04fa-4653-8dcc-4bf6c49d2d25", None),
    ],
)
@pytest.mark.asyncio
async def test_get_login_hint(input: str | None, output: LoginHint | None):
    assert await get_login_hint(input, []) == output


@pytest.mark.asyncio
async def test_get_login_hint_oauth_provider(test_data: TestData):
    oauth_provider = test_data["oauth_providers"]["google"]
    assert (
        await get_login_hint(
            str(oauth_provider.id), list(test_data["oauth_providers"].values())
        )
        == oauth_provider
    )
