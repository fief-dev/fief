import pytest
from starlette.datastructures import FormData

from fief.apps.auth.forms.register import RegisterFormBase, get_register_form_class
from fief.models import UserField, UserFieldType


@pytest.mark.asyncio
class TestGetRegisterFormClass:
    async def test_basic(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.first_name": "Anne",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.first_name.data == "Anne"

    async def test_missing_required_field(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "herminetincture"}),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.first_name.errors == ["This field is required."]

    async def test_invalid_empty_string(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.first_name": "",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.first_name.errors == ["This field is required."]

    async def test_missing_boolean_field(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "herminetincture"}),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.newsletter.data is False

    async def test_provided_boolean_field(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.newsletter": "on",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.newsletter.data is True

    @pytest.mark.parametrize("value", [None, ""])
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        data = {"email": "anne@bretagne.duchy", "password": "herminetincture"}
        if value is not None:
            data["fields.consent"] = value
        form = form_class(FormData(data), meta={"csrf": False})

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.consent.errors == ["This field is required."]

    async def test_required_boolean_field_true(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.consent": "on",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.consent.data is True

    async def test_invalid_choice(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.choice": "d",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.choice.errors == ["Not a valid choice."]

    async def test_valid_choice(self) -> None:
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
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.choice": "a",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.choice.data == "a"

    async def test_phone_number(self) -> None:
        user_fields: list[UserField] = [
            UserField(
                name="Phone number",
                slug="phone_number",
                type=UserFieldType.PHONE_NUMBER,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "herminetincture",
                    "fields.phone_number": "+33102030405",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.phone_number.data == "+33102030405"

    async def test_optional_address(self) -> None:
        user_fields: list[UserField] = [
            UserField(
                name="Address",
                slug="address",
                type=UserFieldType.ADDRESS,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class: type[RegisterFormBase] = await get_register_form_class(
            user_fields, None
        )
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "herminetincture"}),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.address.data is None
