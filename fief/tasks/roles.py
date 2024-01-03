import uuid

import dramatiq

from fief.models import Role, UserPermission
from fief.repositories import (
    RoleRepository,
    UserPermissionRepository,
    UserRoleRepository,
)
from fief.tasks.base import ObjectDoesNotExistTaskError, TaskBase


class OnRoleUpdated(TaskBase):
    __name__ = "on_role_updated"

    async def run(
        self, role_id: str, added_permissions: list[str], deleted_permissions: list[str]
    ):
        async with self.get_main_session() as session:
            role_repository = RoleRepository(session)
            user_role_repository = UserRoleRepository(session)
            user_permission_repository = UserPermissionRepository(session)

            role = await role_repository.get_by_id(uuid.UUID(role_id))

            if role is None:
                raise ObjectDoesNotExistTaskError(Role, role_id)

            # Add newly added permissions to users with this role
            user_roles = await user_role_repository.get_by_role(role.id)
            user_permissions: list[UserPermission] = []
            for user_role in user_roles:
                for added_permission in added_permissions:
                    user_permissions.append(
                        UserPermission(
                            user_id=user_role.user_id,
                            permission_id=uuid.UUID(added_permission),
                            from_role_id=role.id,
                        )
                    )
            await user_permission_repository.create_many(user_permissions)

            # Revoke deleted permissions to users with this role
            for deleted_permission in deleted_permissions:
                await user_permission_repository.delete_by_permission_and_role(
                    uuid.UUID(deleted_permission), role.id
                )


on_role_updated = dramatiq.actor(OnRoleUpdated())
