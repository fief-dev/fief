import uuid

import dramatiq

from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.settings import settings
from fief.tasks.base import TaskBase


class OnAfterForgotPasswordTask(TaskBase):
    __name__ = "on_after_forgot_password"

    async def run(self, user_id: str, workspace_id: str, reset_url: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        user = await self._get_user(uuid.UUID(user_id), workspace)
        tenant = await self._get_tenant(user.tenant_id, workspace)

        translations = user.get_preferred_translations()
        title = translations.gettext("Reset your %(tenant)s's password") % {
            "tenant": tenant.name
        }
        context = {"tenant": tenant, "title": title, "reset_url": reset_url}
        html = self._render_email_template(
            "forgot_password.html", translations, context
        )
        self.email_provider.send_email(
            sender=("contact@fief.dev", None),
            recipient=(user.email, None),
            subject=title,
            html=html,
        )


on_after_forgot_password = dramatiq.actor(
    OnAfterForgotPasswordTask(
        main_async_session_maker, get_workspace_session, settings.get_email_provider()
    )
)
