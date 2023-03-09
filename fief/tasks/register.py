import uuid

import dramatiq

from fief import schemas
from fief.models import UserRole
from fief.repositories import RoleRepository, UserRoleRepository
from fief.services.email_template.contexts import WelcomeContext
from fief.services.email_template.types import EmailTemplateType
from fief.tasks.base import TaskBase, send_task
from fief.tasks.user_permissions import on_user_role_created


class OnAfterRegisterTask(TaskBase):
    __name__ = "on_after_register"

    async def run(self, user_id: str, workspace_id: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))
        user = await self._get_user(uuid.UUID(user_id), workspace)
        tenant = await self._get_tenant(user.tenant_id, workspace)

        # Grant default roles
        async with self.get_workspace_session(workspace) as session:
            role_repository = RoleRepository(session)
            user_role_repository = UserRoleRepository(session)

            default_roles = await role_repository.get_granted_by_default()
            user_roles: list[UserRole] = []
            for role in default_roles:
                existing_user_role = await user_role_repository.get_by_role_and_user(
                    user.id, role.id
                )
                if existing_user_role is None:
                    user_roles.append(UserRole(user_id=user.id, role_id=role.id))
            user_roles = await user_role_repository.create_many(user_roles)
            for user_role in user_roles:
                send_task(
                    on_user_role_created,
                    str(user.id),
                    str(user_role.role_id),
                    str(workspace.id),
                )

        # Send welcome email
        context = WelcomeContext(
            tenant=schemas.tenant.Tenant.from_orm(tenant),
            user=schemas.user.UserEmailContext.from_orm(user),
        )
        async with self._get_email_subject_renderer(
            workspace
        ) as email_subject_renderer:
            subject = await email_subject_renderer.render(
                EmailTemplateType.WELCOME, context
            )

        async with self._get_email_template_renderer(
            workspace
        ) as email_template_renderer:
            html = await email_template_renderer.render(
                EmailTemplateType.WELCOME, context
            )

        self.email_provider.send_email(
            sender=("contact@fief.dev", None),
            recipient=(user.email, None),
            subject=subject,
            html=html,
        )


on_after_register = dramatiq.actor(OnAfterRegisterTask())
