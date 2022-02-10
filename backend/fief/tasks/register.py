import uuid

import dramatiq

from fief.db import get_account_session, global_async_session_maker
from fief.settings import settings
from fief.tasks.base import TaskBase


class OnAfterRegisterTask(TaskBase):
    __name__ = "on_after_register"

    async def run(self, user_id: str, account_id: str):
        account = await self._get_account(uuid.UUID(account_id))
        user = await self._get_user(uuid.UUID(user_id), account)
        tenant = await self._get_tenant(user.tenant_id, account)

        translations = user.get_preferred_translations()
        title = translations.gettext("Welcome to %(tenant)s!") % {"tenant": tenant.name}
        context = {"tenant": tenant, "title": title}
        html = self._render_email_template("welcome.html", translations, context)
        self.email_provider.send_email(
            sender=("contact@fief.dev", None),
            recipient=(user.email, None),
            subject=title,
            html=html,
        )


on_after_register = dramatiq.actor(
    OnAfterRegisterTask(
        global_async_session_maker, get_account_session, settings.get_email_provider()
    )
)
