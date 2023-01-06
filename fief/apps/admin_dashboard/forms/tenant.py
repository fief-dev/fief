from wtforms import BooleanField, StringField, URLField, validators

from fief.forms import ComboboxSelectField, CSRFBaseForm, empty_string_to_none


class BaseTenantForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    registration_allowed = BooleanField("Registration allowed", default=True)
    logo_url = URLField(
        "Logo URL",
        validators=[validators.Optional(), validators.URL(require_tld=False)],
        filters=[empty_string_to_none],
        description="It will be shown on the top left of authentication pages.",
    )
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
