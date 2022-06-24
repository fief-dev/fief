from wtforms import EmailField, HiddenField, PasswordField, validators

from fief.apps.auth.forms.base import BaseForm
from fief.locale import gettext_lazy as _


class ForgotPasswordForm(BaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )


class ResetPasswordForm(BaseForm):
    password = PasswordField(_("New password"), validators=[validators.InputRequired()])
    token = HiddenField(validators=[validators.InputRequired()])
