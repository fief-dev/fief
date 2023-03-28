from wtforms import PasswordField, validators

from fief.forms import CSRFBaseForm
from fief.locale import gettext_lazy as _


class ChangePasswordForm(CSRFBaseForm):
    old_password = PasswordField(
        _("Old password"), validators=[validators.InputRequired()]
    )
    new_password = PasswordField(
        _("New password"), validators=[validators.InputRequired()]
    )
    new_password_confirm = PasswordField(
        _("Confirm new password"), validators=[validators.InputRequired()]
    )
