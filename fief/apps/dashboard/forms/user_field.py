from typing import Any, Type

from fastapi import Request
from wtforms import (
    BooleanField,
    FieldList,
    Form,
    FormField,
    IntegerField,
    SelectField,
    StringField,
    validators,
)
from wtforms.utils import unset_value

from fief.forms import CSRFBaseForm, TimezoneField, empty_string_to_none
from fief.models import UserField, UserFieldType


class FormFieldValueLabelTuple(FormField):
    def process(self, formdata, data=unset_value, extra_filters=None):
        """
        Transform input data in form of a tuple to a dict with value/label.
        """
        data_dict = {}
        if data:
            data_dict = {"value": data[0], "label": data[1]}

        return super().process(formdata, data_dict, extra_filters)

    def populate_obj(self, obj, name):
        """
        Transform data labelled with value/label to a tuple.
        """
        setattr(obj, name, (self.form.value.data, self.form.label.data))

    @property
    def data(self):
        return (self.form.value.data, self.form.label.data)


class SettableDict(dict):
    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value


class FormFieldPopulateJSON(FormField):
    def populate_obj(self, obj, name):
        d = SettableDict()
        self.form.populate_obj(d)
        setattr(obj, name, d)


class UserFieldConfigurationBase(Form):
    at_registration = BooleanField("Ask at registration")
    at_update = BooleanField("Ask at profile update")
    required = BooleanField("Required")

    def set_dynamic_parameters(self):
        pass


class UserFieldConfigurationString(UserFieldConfigurationBase):
    default = StringField("Default value", filters=[empty_string_to_none])


class UserFieldConfigurationInteger(UserFieldConfigurationBase):
    default = IntegerField("Default value")


class UserFieldConfigurationBoolean(UserFieldConfigurationBase):
    default = BooleanField("Enabled")


class UserFieldConfigurationDate(UserFieldConfigurationBase):
    pass


class UserFieldConfigurationDateTime(UserFieldConfigurationBase):
    pass


class UserFieldConfigurationChoiceItem(Form):
    value = StringField(render_kw={"placeholder": "Value"})
    label = StringField(render_kw={"placeholder": "Label"})


class UserFieldConfigurationChoice(UserFieldConfigurationBase):
    choices = FieldList(
        FormFieldValueLabelTuple(UserFieldConfigurationChoiceItem),
        "Choices",
        min_entries=1,
    )
    default = SelectField("Default value")

    def set_dynamic_parameters(self):
        choices = self.data["choices"]
        if choices is not None:
            self.default.choices = [("", "")] + [
                (key, value) for (key, value) in choices if value is not None
            ]


class UserFieldConfigurationPhoneNumber(UserFieldConfigurationBase):
    pass


class UserFieldConfigurationAddress(UserFieldConfigurationBase):
    pass


class UserFieldConfigurationTimezone(UserFieldConfigurationBase):
    default = TimezoneField("Default value")


CONFIGURATION_FORM_CLASS_MAP: dict[UserFieldType, type[Form]] = {
    UserFieldType.STRING: UserFieldConfigurationString,
    UserFieldType.INTEGER: UserFieldConfigurationInteger,
    UserFieldType.BOOLEAN: UserFieldConfigurationBoolean,
    UserFieldType.DATE: UserFieldConfigurationDate,
    UserFieldType.DATETIME: UserFieldConfigurationDateTime,
    UserFieldType.CHOICE: UserFieldConfigurationChoice,
    UserFieldType.PHONE_NUMBER: UserFieldConfigurationPhoneNumber,
    UserFieldType.ADDRESS: UserFieldConfigurationAddress,
    UserFieldType.TIMEZONE: UserFieldConfigurationTimezone,
}


class BaseUserFieldForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    slug = StringField("Slug", validators=[validators.InputRequired()])


class UserFieldCreateForm(BaseUserFieldForm):
    type = SelectField(
        "Type",
        choices=UserFieldType.choices(),
        coerce=UserFieldType.coerce,
        default=UserFieldType.STRING.value,
        validators=[validators.InputRequired()],
    )

    @classmethod
    async def get_form_class(cls, request: Request) -> Type["UserFieldCreateForm"]:
        formdata = None
        if request.method in {"POST", "PUT", "PATCH"}:
            formdata = await request.form()
        base_form = cls(formdata, meta={"request": request})
        field_type = base_form.data["type"]
        if field_type is not None and field_type in CONFIGURATION_FORM_CLASS_MAP:
            configuration_form_class = CONFIGURATION_FORM_CLASS_MAP[field_type]

            class UserFieldForm(UserFieldCreateForm):
                configuration = FormFieldPopulateJSON(configuration_form_class)

            return UserFieldForm
        return cls


class UserFieldUpdateForm(BaseUserFieldForm):
    @classmethod
    async def get_form_class(cls, user_field: UserField) -> Type["UserFieldUpdateForm"]:
        class UserFieldForm(UserFieldUpdateForm):
            configuration = FormFieldPopulateJSON(
                CONFIGURATION_FORM_CLASS_MAP[user_field.type]
            )

        return UserFieldForm
