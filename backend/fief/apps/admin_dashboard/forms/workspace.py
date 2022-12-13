from wtforms import (
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    validators,
    widgets,
)

from fief.db.types import SSL_MODES, DatabaseType
from fief.forms import CSRFBaseForm


class WorkspaceCreateStep1Form(CSRFBaseForm):
    name = StringField(
        "Name of your workspace", validators=[validators.InputRequired()]
    )


class WorkspaceCreateStep2Form(CSRFBaseForm):
    database = RadioField(
        choices=[("cloud", "cloud"), ("custom", "custom")],
        validators=[validators.InputRequired()],
    )


class WorkspaceCreateStep3Form(CSRFBaseForm):
    database_type = SelectField(
        label="Database type",
        choices=DatabaseType.get_choices(),
        default=DatabaseType.POSTGRESQL.value,
        validators=[validators.InputRequired()],
    )
    database_host = StringField(label="Host", validators=[validators.InputRequired()])
    database_port = IntegerField(label="Port", validators=[validators.InputRequired()])
    database_username = StringField(
        label="Username", validators=[validators.InputRequired()]
    )
    database_password = PasswordField(
        label="Password",
        validators=[validators.InputRequired()],
        widget=widgets.PasswordInput(hide_value=False),
    )
    database_name = StringField(
        label="Database name", validators=[validators.InputRequired()]
    )
    database_ssl_mode = SelectField(
        label="SSL mode", validators=[validators.InputRequired()]
    )

    def prefill_from_database_type(self):
        database_type = DatabaseType[self.database_type.data]
        ssl_modes_enum = SSL_MODES[database_type]
        self.database_ssl_mode.choices = ssl_modes_enum.get_choices()
        if not self.database_ssl_mode.data:
            self.database_ssl_mode.process_data(self.database_ssl_mode.choices[0][0])


class WorkspaceCreateStep4Form(CSRFBaseForm):
    pass
