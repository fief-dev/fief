from typing import List, Optional

import pytest
from pydantic import ValidationError

from fief.dependencies.user_field import get_user_create_model
from fief.models import UserField, UserFieldType
from fief.schemas.user import UserCreate


@pytest.mark.asyncio
class TestGetUserCreateModel:
    async def test_basic(self):
        user_fields: List[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        assert issubclass(model, UserCreate)

        user_create = model(
            email="anne@bretagne.duchy",
            password="hermine",
            first_name="Anne",
        )

        assert isinstance(user_create, model)
        assert user_create.first_name == "Anne"

    async def test_missing_required_field(self):
        user_fields: List[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            model(email="anne@bretagne.duchy", password="hermine")

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("first_name",)

    async def test_invalid_empty_string(self):
        user_fields: List[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            model(email="anne@bretagne.duchy", password="hermine", first_name="")

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("first_name",)

    async def test_missing_boolean_field(self):
        user_fields: List[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(email="anne@bretagne.duchy", password="hermine")

        assert user_create.newsletter is False

    async def test_provided_boolean_field(self):
        user_fields: List[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(
            email="anne@bretagne.duchy", password="hermine", newsletter="on"
        )

        assert user_create.newsletter is True

    @pytest.mark.parametrize("value", [None, "off"])
    async def test_required_boolean_field_false(self, value: Optional[str]):
        user_fields: List[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            values = {
                "email": "anne@bretagne.duchy",
                "password": "hermine",
            }
            if value is not None:
                values["consent"] = value
            model(**values)

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("consent",)
        assert errors[0]["type"] == "value_error.boolean.must_be_true"

    async def test_required_boolean_field_true(self):
        user_fields: List[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "editable": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(
            email="anne@bretagne.duchy", password="hermine", consent="on"
        )

        assert user_create.consent is True
