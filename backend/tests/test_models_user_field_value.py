from typing import Any

import pytest

from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_field_value_alias,expected",
    [
        pytest.param("regular_given_name", "Anne", id="STRING"),
        pytest.param("regular_gender", "female", id="CHOICE"),
        pytest.param("regular_phone_number", "+33642424242", id="PHONE_NUMBER"),
        pytest.param("regular_phone_number_verified", True, id="BOOLEAN"),
    ],
)
async def test_get_value(
    user_field_value_alias: str, expected: Any, test_data: TestData
):
    user_field_value = test_data["user_field_values"][user_field_value_alias]
    assert user_field_value.get_value() == expected
