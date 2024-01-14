from fief.models import Permission, Role
from fief.repositories import PermissionRepository, RoleRepository

ADMIN_PERMISSION_CODENAME = "fief:admin"
ADMIN_PERMISSION_NAME = "Fief Administrator"
ADMIN_ROLE_NAME = "Administrator"


async def init_admin_role(
    role_repository: RoleRepository, permission_repository: PermissionRepository
) -> Role:
    permission = await permission_repository.create(
        Permission(name=ADMIN_PERMISSION_NAME, codename=ADMIN_PERMISSION_CODENAME)
    )
    role = await role_repository.create(
        Role(name=ADMIN_ROLE_NAME, permissions=[permission], user_permissions=[])
    )
    return role
