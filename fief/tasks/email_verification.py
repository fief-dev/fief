import uuid

import dramatiq

from fief import schemas
from fief.logger import logger
from fief.models import EmailVerification
from fief.repositories import EmailVerificationRepository
from fief.services.email import Null
from fief.services.email_template.contexts import VerifyEmailContext
from fief.services.email_template.types import EmailTemplateType
from fief.tasks.base import ObjectDoesNotExistTaskError, TaskBase


class OnEmailVerificationRequestedTask(TaskBase):
    __name__ = "on_email_verification_requested"

    async def run(self, email_verification_id: str, workspace_id: str, code: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        async with self.get_workspace_session(workspace) as session:
            email_verification_repository = EmailVerificationRepository(session)
            email_verification = await email_verification_repository.get_by_id(
                uuid.UUID(email_verification_id)
            )

            if email_verification is None:
                raise ObjectDoesNotExistTaskError(
                    EmailVerification, email_verification_id
                )

            user = email_verification.user
            tenant = await self._get_tenant(user.tenant_id, workspace)

            context = VerifyEmailContext(
                tenant=schemas.tenant.Tenant.model_validate(tenant),
                user=schemas.user.UserEmailContext.model_validate(user),
                code=code,
            )

            async with self._get_email_subject_renderer(
                workspace
            ) as email_subject_renderer:
                subject = await email_subject_renderer.render(
                    EmailTemplateType.VERIFY_EMAIL, context
                )

            async with self._get_email_template_renderer(
                workspace
            ) as email_template_renderer:
                html = await email_template_renderer.render(
                    EmailTemplateType.VERIFY_EMAIL, context
                )

            self.email_provider.send_email(
                sender=tenant.get_email_sender(),
                recipient=(email_verification.email, None),
                subject=subject,
                html=html,
            )

            if isinstance(self.email_provider, Null):
                logger.warning(
                    "Email verification requested with NULL email provider",
                    email_verification_id=email_verification_id,
                    code=code,
                )


on_email_verification_requested = dramatiq.actor(OnEmailVerificationRequestedTask())
