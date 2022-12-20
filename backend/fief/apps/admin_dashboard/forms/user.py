from wtforms import EmailField, Form, FormField, PasswordField, validators, widgets

from fief.forms import (
    ComboboxSelectField,
    CSRFBaseForm,
    empty_string_to_none,
    get_form_field,
)
from fief.models import UserField


class BaseUserForm(CSRFBaseForm):
    email = EmailField(
        "Email address", validators=[validators.InputRequired(), validators.Email()]
    )

    @classmethod
    async def get_form_class(
        cls, user_fields: list[UserField]
    ) -> type["UserCreateForm"]:
        class UserFormFields(Form):
            pass

        for field in user_fields:
            setattr(UserFormFields, field.slug, get_form_field(field))

        class UserForm(cls):  # type: ignore
            fields = FormField(UserFormFields)

        return UserForm


class UserCreateForm(BaseUserForm):
    password = PasswordField(
        "Password",
        validators=[validators.InputRequired()],
        widget=widgets.PasswordInput(hide_value=False),
    )
    tenant_id = ComboboxSelectField(
        "Tenant",
        query_endpoint_path="/admin/tenants/",
        validators=[validators.InputRequired(), validators.UUID()],
    )


class UserUpdateForm(BaseUserForm):
    password = PasswordField(
        "Password",
        filters=(empty_string_to_none,),
        widget=widgets.PasswordInput(hide_value=False),
    )
