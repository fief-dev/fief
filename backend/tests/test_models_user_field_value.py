from datetime import date, datetime
from typing import Any

import pytest

from fief.models import UserField, UserFieldType, UserFieldValue


@pytest.mark.parametrize(
    "user_field_type,value,field",
    [
        pytest.param(UserFieldType.STRING, "VALUE", "value_string", id="STRING"),
        pytest.param(UserFieldType.CHOICE, "VALUE", "value_string", id="CHOICE"),
        pytest.param(
            UserFieldType.PHONE_NUMBER, "VALUE", "value_string", id="PHONE_NUMBER"
        ),
        pytest.param(UserFieldType.LOCALE, "VALUE", "value_string", id="LOCALE"),
        pytest.param(UserFieldType.TIMEZONE, "VALUE", "value_string", id="TIMEZONE"),
        pytest.param(UserFieldType.INTEGER, 123, "value_integer", id="INTEGER"),
        pytest.param(UserFieldType.BOOLEAN, True, "value_boolean", id="BOOLEAN"),
        pytest.param(UserFieldType.DATE, date.today(), "value_date", id="DATE"),
        pytest.param(
            UserFieldType.DATETIME, datetime.now(), "value_datetime", id="DATETIME"
        ),
        pytest.param(UserFieldType.ADDRESS, {"foo": "bar"}, "value_json", id="ADDRESS"),
    ],
)
def test_value_getter(user_field_type: UserFieldType, value: Any, field: str):
    user_field = UserField(
        name="Test",
        slug="test",
        type=user_field_type,
        configuration={
            "choices": None,
            "at_registration": False,
            "required": False,
            "editable": False,
            "default": None,
        },
    )
    user_field_value = UserFieldValue(user_field=user_field)
    setattr(user_field_value, field, value)

    assert user_field_value.value == value


@pytest.mark.parametrize(
    "user_field_type,value,expected_field",
    [
        pytest.param(UserFieldType.STRING, "VALUE", "value_string", id="STRING"),
        pytest.param(UserFieldType.CHOICE, "VALUE", "value_string", id="CHOICE"),
        pytest.param(
            UserFieldType.PHONE_NUMBER, "VALUE", "value_string", id="PHONE_NUMBER"
        ),
        pytest.param(UserFieldType.LOCALE, "VALUE", "value_string", id="LOCALE"),
        pytest.param(UserFieldType.TIMEZONE, "VALUE", "value_string", id="TIMEZONE"),
        pytest.param(UserFieldType.INTEGER, 123, "value_integer", id="INTEGER"),
        pytest.param(UserFieldType.BOOLEAN, True, "value_boolean", id="BOOLEAN"),
        pytest.param(UserFieldType.DATE, date.today(), "value_date", id="DATE"),
        pytest.param(
            UserFieldType.DATETIME, datetime.now(), "value_datetime", id="DATETIME"
        ),
        pytest.param(UserFieldType.ADDRESS, {"foo": "bar"}, "value_json", id="ADDRESS"),
    ],
)
def test_value_setter(user_field_type: UserFieldType, value: Any, expected_field: str):
    user_field = UserField(
        name="Test",
        slug="test",
        type=user_field_type,
        configuration={
            "choices": None,
            "at_registration": False,
            "required": False,
            "editable": False,
            "default": None,
        },
    )
    user_field_value = UserFieldValue(user_field=user_field)
    user_field_value.value = value

    assert getattr(user_field_value, expected_field) == value
