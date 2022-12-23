from wtforms import BooleanField, StringField, validators

from fief.forms import ComboboxSelectMultipleField, CSRFBaseForm


class BaseRoleForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    granted_by_default = BooleanField(
        "Granted by default",
        description="When enabled, the role will automatically be assigned to users when they register.",
    )
    permissions = ComboboxSelectMultipleField(
        "Permissions",
        query_endpoint_path="/admin/permissions/",
        label_attr="codename",
        validators=[validators.InputRequired()],
        choices=[],
        validate_choice=False,
    )


class RoleCreateForm(BaseRoleForm):
    pass


class RoleUpdateForm(BaseRoleForm):
    pass
