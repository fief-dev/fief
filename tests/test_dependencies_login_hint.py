import uuid

import pytest

from fief.dependencies.login_hint import LoginHint, get_login_hint


@pytest.mark.parametrize(
    "input,output",
    [
        (None, None),
        ("INVALID_VALUE", None),
        ("anne@bretagne.duchy", "anne@bretagne.duchy"),
        ("anne%40bretagne.duchy", "anne@bretagne.duchy"),
        (
            "b0133c88-04fa-4653-8dcc-4bf6c49d2d25",
            uuid.UUID("b0133c88-04fa-4653-8dcc-4bf6c49d2d25"),
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_login_hint(input: str | None, output: LoginHint | None):
    assert await get_login_hint(input) == output
