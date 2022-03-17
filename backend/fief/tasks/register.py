import uuid

import dramatiq

from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.settings import settings
from fief.tasks.base import TaskBase


class OnAfterRegisterTask(TaskBase):
    __name__ = "on_after_register"

    async def run(self, user_id: str, workspace_id: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        user = await self._get_user(uuid.UUID(user_id), workspace)
        tenant = await self._get_tenant(user.tenant_id, workspace)

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
        main_async_session_maker, get_workspace_session, settings.get_email_provider()
    )
)
