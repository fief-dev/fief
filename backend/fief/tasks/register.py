import uuid
from typing import List

import dramatiq

from fief.models import UserRole
from fief.repositories import RoleRepository, UserRoleRepository
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
            user_roles: List[UserRole] = []
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


on_after_register = dramatiq.actor(OnAfterRegisterTask())
