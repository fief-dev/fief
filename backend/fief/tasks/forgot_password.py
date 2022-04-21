import uuid

import dramatiq

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


on_after_forgot_password = dramatiq.actor(OnAfterForgotPasswordTask())
