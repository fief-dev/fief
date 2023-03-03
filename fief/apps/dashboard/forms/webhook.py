from wtforms import URLField, validators

from fief.forms import CSRFBaseForm, SelectMultipleFieldCheckbox
from fief.services.webhooks.models import WEBHOOK_EVENTS


class BaseWebhookForm(CSRFBaseForm):
    url = URLField(
        "URL",
        validators=[validators.InputRequired(), validators.URL(require_tld=False)],
    )
    events = SelectMultipleFieldCheckbox(
        "Events to notify", choices=[event.key() for event in WEBHOOK_EVENTS]
    )


class WebhookCreateForm(BaseWebhookForm):
    pass


class WebhookUpdateForm(BaseWebhookForm):
    pass
