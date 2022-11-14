import uuid
from typing import List

import dramatiq

from fief.models import UserPermission
from fief.repositories import RoleRepository, UserPermissionRepository
from fief.tasks.base import TaskBase, TaskError


class OnUserRoleCreated(TaskBase):
    __name__ = "on_user_role_created"

    async def run(self, user_id: str, role_id: str, workspace_id: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))

        async with self.get_workspace_session(workspace) as session:
            role_repository = RoleRepository(session)
            user_permission_repository = UserPermissionRepository(session)

            role = await role_repository.get_by_id(uuid.UUID(role_id))

            if role is None:
                raise TaskError(f"Role {role_id} doesn't exist.")

            user_permissions: List[UserPermission] = []
            for permission in role.permissions:
                user_permissions.append(
                    UserPermission(
                        user_id=uuid.UUID(user_id),
                        permission_id=permission.id,
                        from_role_id=role.id,
                    )
                )
            await user_permission_repository.create_many(user_permissions)


class OnUserRoleDeleted(TaskBase):
    __name__ = "on_user_role_deleted"

    async def run(self, user_id: str, role_id: str, workspace_id: str):
        workspace = await self._get_workspace(uuid.UUID(workspace_id))

        async with self.get_workspace_session(workspace) as session:
            user_permission_repository = UserPermissionRepository(session)
            await user_permission_repository.delete_by_user_and_role(
                uuid.UUID(user_id), uuid.UUID(role_id)
            )


on_user_role_created = dramatiq.actor(OnUserRoleCreated())
on_user_role_deleted = dramatiq.actor(OnUserRoleDeleted())
