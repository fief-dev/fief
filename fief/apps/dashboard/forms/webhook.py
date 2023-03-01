from wtforms import URLField, validators

from fief.forms import CSRFBaseForm, SelectMultipleFieldCheckbox
from fief.services.webhooks.models import WEBHOOK_OBJECTS, WebhookEventType


class BaseWebhookForm(CSRFBaseForm):
    url = URLField(
        "URL",
        validators=[validators.InputRequired(), validators.URL(require_tld=False)],
    )
    events = SelectMultipleFieldCheckbox(
        "Events to notify", choices=WebhookEventType.get_choices()
    )
    objects = SelectMultipleFieldCheckbox(
        "Objects to receive notifications for",
        choices=WEBHOOK_OBJECTS,
        description="Only applicable for Object Created, Updated and Deleted events.",
    )


class WebhookCreateForm(BaseWebhookForm):
    pass


class WebhookUpdateForm(BaseWebhookForm):
    pass
