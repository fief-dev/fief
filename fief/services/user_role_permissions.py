from fief.models import Role, User, UserPermission
from fief.repositories import UserPermissionRepository


class UserRolePermissionsService:
    def __init__(self, user_permission_repository: UserPermissionRepository) -> None:
        self.user_permission_repository = user_permission_repository

    async def add_role_permissions(self, user: User, role: Role) -> None:
        user_permissions: list[UserPermission] = []
        for permission in role.permissions:
            user_permissions.append(
                UserPermission(
                    user_id=user.id,
                    permission_id=permission.id,
                    from_role_id=role.id,
                )
            )
        await self.user_permission_repository.create_many(user_permissions)

    async def delete_role_permissions(self, user: User, role: Role) -> None:
        await self.user_permission_repository.delete_by_user_and_role(user.id, role.id)
