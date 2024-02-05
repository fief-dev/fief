import uuid

import dramatiq

from fief import schemas
from fief.services.email_template.contexts import WelcomeContext
from fief.services.email_template.types import EmailTemplateType
from fief.tasks.base import TaskBase


class OnAfterRegisterTask(TaskBase):
    __name__ = "on_after_register"

    async def run(self, user_id: str):
        user = await self._get_user(uuid.UUID(user_id))
        tenant = await self._get_tenant(user.tenant_id)

        # Send welcome email
        context = WelcomeContext(
            tenant=schemas.tenant.Tenant.model_validate(tenant),
            user=schemas.user.UserEmailContext.model_validate(user),
        )
        async with self._get_email_subject_renderer() as email_subject_renderer:
            subject = await email_subject_renderer.render(
                EmailTemplateType.WELCOME, context
            )

        async with self._get_email_template_renderer() as email_template_renderer:
            html = await email_template_renderer.render(
                EmailTemplateType.WELCOME, context
            )

        self.email_provider.send_email(
            sender=tenant.get_email_sender(),
            recipient=(user.email, None),
            subject=subject,
            html=html,
        )


on_after_register = dramatiq.actor(OnAfterRegisterTask())
