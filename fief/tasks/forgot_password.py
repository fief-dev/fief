import uuid

import dramatiq

from fief import schemas
from fief.services.email_template.contexts import ForgotPasswordContext
from fief.services.email_template.types import EmailTemplateType
from fief.settings import settings
from fief.tasks.base import TaskBase


class OnAfterForgotPasswordTask(TaskBase):
    __name__ = "on_after_forgot_password"

    async def run(self, user_id: str, workspace_id: str, reset_url: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        user = await self._get_user(uuid.UUID(user_id), workspace)
        tenant = await self._get_tenant(user.tenant_id, workspace)

        context = ForgotPasswordContext(
            tenant=schemas.tenant.Tenant.from_orm(tenant),
            user=schemas.user.UserEmailContext.from_orm(user),
            reset_url=reset_url,
        )

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
            sender=(settings.default_from_email, settings.default_from_name),
            recipient=(user.email, None),
            subject=subject,
            html=html,
        )


on_after_forgot_password = dramatiq.actor(OnAfterForgotPasswordTask())
