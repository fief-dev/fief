
import pytest
from pydantic import ValidationError

from fief.dependencies.user_field import get_user_create_model
from fief.models import UserField, UserFieldType
from fief.schemas.user import UserCreate


@pytest.mark.asyncio
class TestGetUserCreateModel:
    async def test_basic(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
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
            fields={
                "first_name": "Anne",
            },
        )

        assert isinstance(user_create, model)
        assert user_create.fields.first_name == "Anne"

    async def test_missing_required_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            model(email="anne@bretagne.duchy", password="hermine", fields={})

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (
            "fields",
            "first_name",
        )

    async def test_invalid_empty_string(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            model(
                email="anne@bretagne.duchy",
                password="hermine",
                fields={"first_name": ""},
            )

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (
            "fields",
            "first_name",
        )

    async def test_missing_boolean_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(email="anne@bretagne.duchy", password="hermine", fields={})

        assert user_create.fields.newsletter is False

    async def test_provided_boolean_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(
            email="anne@bretagne.duchy", password="hermine", fields={"newsletter": "on"}
        )

        assert user_create.fields.newsletter is True

    @pytest.mark.parametrize("value", [None, "off"])
    async def test_required_boolean_field_false(self, value: str | None):
        user_fields: list[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            fields = {}
            if value is not None:
                fields["consent"] = value
            model(email="anne@bretagne.duchy", password="hermine", fields=fields)

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (
            "fields",
            "consent",
        )
        assert errors[0]["type"] == "value_error.boolean.must_be_true"

    async def test_required_boolean_field_true(self):
        user_fields: list[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(
            email="anne@bretagne.duchy", password="hermine", fields={"consent": "on"}
        )

        assert user_create.fields.consent is True

    async def test_invalid_choice(self):
        user_fields: list[UserField] = [
            UserField(
                name="Choice",
                slug="choice",
                type=UserFieldType.CHOICE,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": [("a", "A"), ("b", "B"), ("c", "C")],
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        with pytest.raises(ValidationError) as e:
            model(
                email="anne@bretagne.duchy", password="hermine", fields={"choice": "d"}
            )

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (
            "fields",
            "choice",
        )
        assert errors[0]["type"] == "type_error.enum"

    async def test_valid_choice(self):
        user_fields: list[UserField] = [
            UserField(
                name="Choice",
                slug="choice",
                type=UserFieldType.CHOICE,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": [("a", "A"), ("b", "B"), ("c", "C")],
                },
            ),
        ]
        model = await get_user_create_model(user_fields)

        user_create = model(
            email="anne@bretagne.duchy", password="hermine", fields={"choice": "a"}
        )

        assert user_create.fields.choice == "a"
