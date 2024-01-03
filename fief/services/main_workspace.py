import functools

from fief.crypto.token import get_token_hash
from fief.db.main import get_single_main_async_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.users import get_user_manager
from fief.models import AdminAPIKey, User
from fief.repositories import (
    AdminAPIKeyRepository,
    EmailVerificationRepository,
    TenantRepository,
    UserFieldRepository,
    UserRepository,
)
from fief.schemas.user import UserCreateAdmin
from fief.services.webhooks.trigger import trigger_webhooks
from fief.tasks import send_task


class MainWorkspaceError(Exception):
    pass


class MainWorkspaceDoesNotHaveDefaultTenant(MainWorkspaceError):
    pass


class CreateMainFiefUserError(MainWorkspaceError):
    pass


class MainFiefAdminApiKeyAlreadyExists(MainWorkspaceError):
    pass


async def create_admin(email: str, password: str | None = None) -> User:
    async with get_single_main_async_session() as session:
        tenant_repository = TenantRepository(session)
        tenant = await tenant_repository.get_default()

        if tenant is None:
            raise MainWorkspaceDoesNotHaveDefaultTenant()

        user_repository = UserRepository(session)
        email_verification_repository = EmailVerificationRepository(session)
        user_fields = await UserFieldRepository(session).all()
        audit_logger = await get_audit_logger(None, None)

        user_manager = await get_user_manager(
            user_repository,
            email_verification_repository,
            user_fields,
            send_task,
            audit_logger,
            functools.partial(trigger_webhooks, send_task=send_task),
        )

        if password is None:
            password = user_manager.password_helper.generate()

        user = await user_manager.create(
            UserCreateAdmin(
                email=email,
                password=password,
                email_verified=True,
                tenant_id=tenant.id,
            ),
            tenant.id,
        )

    return user


async def create_admin_api_key(token: str) -> AdminAPIKey:
    async with get_single_main_async_session() as session:
        admin_api_key_repository = AdminAPIKeyRepository(session)

        token_hash = get_token_hash(token)
        admin_api_key = await admin_api_key_repository.get_by_token(token_hash)

        if admin_api_key is not None:
            raise MainFiefAdminApiKeyAlreadyExists()

        admin_api_key = AdminAPIKey(name="Environment variable key", token=token_hash)
        await admin_api_key_repository.create(admin_api_key)

    return admin_api_key
