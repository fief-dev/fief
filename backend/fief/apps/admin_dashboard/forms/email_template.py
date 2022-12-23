from wtforms import StringField, TextAreaField

from fief.forms import CSRFBaseForm


class EmailTemplateUpdateForm(CSRFBaseForm):
    subject = StringField("Subject")
    content = TextAreaField("Content")
