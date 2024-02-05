from fief import schemas, tasks
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, Role, User, UserRole
from fief.repositories import UserPermissionRepository, UserRoleRepository
from fief.services.user_role_permissions import UserRolePermissionsService
from fief.services.webhooks.models import UserRoleCreated, UserRoleDeleted
from fief.services.webhooks.trigger import TriggerWebhooks
from fief.tasks import SendTask


class UserRolesError(Exception):
    ...


class UserRoleAlreadyExists(UserRolesError):
    ...


class UserRoleDoesNotExist(UserRolesError):
    ...


class UserRolesService:
    def __init__(
        self,
        user_role_repository: UserRoleRepository,
        user_permission_repository: UserPermissionRepository,
        audit_logger: AuditLogger,
        trigger_webhooks: TriggerWebhooks,
        send_task: SendTask,
    ) -> None:
        self.user_role_repository = user_role_repository
        self.user_permission_repository = user_permission_repository
        self.audit_logger = audit_logger
        self.trigger_webhooks = trigger_webhooks
        self.send_task = send_task
        self.user_role_permissions = UserRolePermissionsService(
            user_permission_repository
        )

    async def add_role(
        self, user: User, role: Role, *, run_in_worker: bool = True
    ) -> UserRole:
        existing_user_role = await self.user_role_repository.get_by_role_and_user(
            user.id, role.id
        )
        if existing_user_role is not None:
            raise UserRoleAlreadyExists()

        user_role = UserRole(user_id=user.id, role=role)
        await self.user_role_repository.create(user_role)
        self.audit_logger.log_object_write(
            AuditLogMessage.OBJECT_CREATED,
            user_role,
            subject_user_id=user.id,
            role_id=str(role.id),
        )
        self.trigger_webhooks(UserRoleCreated, user_role, schemas.user_role.UserRole)

        if run_in_worker:
            self.send_task(tasks.on_user_role_created, str(user.id), str(role.id))
        else:
            await self.user_role_permissions.add_role_permissions(user, role)

        return user_role

    async def delete_role(
        self, user: User, role: Role, *, run_in_worker: bool = True
    ) -> None:
        user_role = await self.user_role_repository.get_by_role_and_user(
            user.id, role.id
        )
        if user_role is None:
            raise UserRoleDoesNotExist()

        await self.user_role_repository.delete(user_role)
        self.audit_logger.log_object_write(
            AuditLogMessage.OBJECT_DELETED,
            user_role,
            subject_user_id=user.id,
            role_id=str(role.id),
        )
        self.trigger_webhooks(UserRoleDeleted, user_role, schemas.user_role.UserRole)

        self.send_task(tasks.on_user_role_deleted, str(user.id), str(role.id))

        if run_in_worker:
            self.send_task(tasks.on_user_role_deleted, str(user.id), str(role.id))
        else:
            await self.user_role_permissions.delete_role_permissions(user, role)
