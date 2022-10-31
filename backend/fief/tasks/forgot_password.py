import uuid

import dramatiq

from fief.services.email_template import EmailTemplateType, ForgotPasswordContext
from fief.tasks.base import TaskBase


class OnAfterForgotPasswordTask(TaskBase):
    __name__ = "on_after_forgot_password"

    async def run(self, user_id: str, workspace_id: str, reset_url: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        user = await self._get_user(uuid.UUID(user_id), workspace)
        tenant = await self._get_tenant(user.tenant_id, workspace)

        context = ForgotPasswordContext(tenant=tenant, user=user, reset_url=reset_url)

        async with self._get_email_subject_renderer(
            workspace
        ) as email_subject_renderer:
            subject = await email_subject_renderer.render(
                EmailTemplateType.FORGOT_PASSWORD, context
            )

        async with self._get_email_template_renderer(
            workspace
        ) as email_template_renderer:
            html = await email_template_renderer.render(
                EmailTemplateType.FORGOT_PASSWORD, context
            )

        self.email_provider.send_email(
            sender=("contact@fief.dev", None),
            recipient=(user.email, None),
            subject=subject,
            html=html,
        )


on_after_forgot_password = dramatiq.actor(OnAfterForgotPasswordTask())
