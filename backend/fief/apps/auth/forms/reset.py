from wtforms import EmailField, HiddenField, PasswordField, validators

from fief.apps.auth.forms.base import CSRFBaseForm
from fief.locale import gettext_lazy as _


class ForgotPasswordForm(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )


class ResetPasswordForm(CSRFBaseForm):
    password = PasswordField(_("New password"), validators=[validators.InputRequired()])
    token = HiddenField(validators=[validators.InputRequired()])
