from wtforms import EmailField, HiddenField, PasswordField, validators, widgets

from fief.forms import CSRFBaseForm, PasswordValidator
from fief.locale import gettext_lazy as _


class ForgotPasswordForm(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )


class ResetPasswordForm(CSRFBaseForm):
    password = PasswordField(
        _("New password"),
        widget=widgets.PasswordInput(hide_value=False),
        validators=[validators.InputRequired(), PasswordValidator()],
    )
    token = HiddenField(validators=[validators.InputRequired()])
