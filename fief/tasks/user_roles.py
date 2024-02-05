import uuid

import dramatiq

from fief.models import Role, User
from fief.repositories import RoleRepository, UserPermissionRepository, UserRepository
from fief.services.user_role_permissions import UserRolePermissionsService
from fief.tasks.base import ObjectDoesNotExistTaskError, TaskBase


class OnUserRoleCreated(TaskBase):
    __name__ = "on_user_role_created"

    async def run(self, user_id: str, role_id: str):
        async with self.get_main_session() as session:
            role_repository = RoleRepository(session)
            user_repository = UserRepository(session)

            role = await role_repository.get_by_id(uuid.UUID(role_id))
            if role is None:
                raise ObjectDoesNotExistTaskError(Role, role_id)

            user = await user_repository.get_by_id(uuid.UUID(user_id))
            if user is None:
                raise ObjectDoesNotExistTaskError(User, user_id)

            user_permission_repository = UserPermissionRepository(session)
            user_role_permissions = UserRolePermissionsService(
                user_permission_repository
            )
            await user_role_permissions.add_role_permissions(user, role)


class OnUserRoleDeleted(TaskBase):
    __name__ = "on_user_role_deleted"

    async def run(self, user_id: str, role_id: str):
        async with self.get_main_session() as session:
            role_repository = RoleRepository(session)
            user_repository = UserRepository(session)

            role = await role_repository.get_by_id(uuid.UUID(role_id))
            if role is None:
                raise ObjectDoesNotExistTaskError(Role, role_id)

            user = await user_repository.get_by_id(uuid.UUID(user_id))
            if user is None:
                raise ObjectDoesNotExistTaskError(User, user_id)

            user_permission_repository = UserPermissionRepository(session)
            user_role_permissions = UserRolePermissionsService(
                user_permission_repository
            )
            await user_role_permissions.delete_role_permissions(user, role)


on_user_role_created = dramatiq.actor(OnUserRoleCreated())
on_user_role_deleted = dramatiq.actor(OnUserRoleDeleted())
