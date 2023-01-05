from wtforms import BooleanField, StringField, validators

from fief.forms import ComboboxSelectField, CSRFBaseForm, empty_string_to_none


class BaseTenantForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    registration_allowed = BooleanField("Registration allowed", default=True)
    theme = ComboboxSelectField(
        "UI Theme",
        query_endpoint_path="/admin/customization/themes/",
        validators=[validators.Optional(), validators.UUID()],
        filters=[empty_string_to_none],
        description="If left empty, the default theme will be used.",
    )


class TenantCreateForm(BaseTenantForm):
    pass


class TenantUpdateForm(BaseTenantForm):
    pass
