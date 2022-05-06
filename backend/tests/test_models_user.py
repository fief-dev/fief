import pytest

from tests.data import TestData


@pytest.mark.asyncio
async def test_get_fields(test_data: TestData):
    user = test_data["users"]["regular"]
    assert user.get_fields() == {
        "gender": "female",
        "given_name": "Anne",
        "phone_number": "+33642424242",
        "phone_number_verified": True,
    }
