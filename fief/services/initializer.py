import functools
from typing import TYPE_CHECKING

from fief.crypto.token import get_token_hash
from fief.db import AsyncEngine, AsyncSession
from fief.db.main import create_main_async_session_maker
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.users import get_user_manager
from fief.models import AdminAPIKey, Client, Permission, Role, Tenant, Theme, User
from fief.repositories import (
    AdminAPIKeyRepository,
    ClientRepository,
    EmailTemplateRepository,
    EmailVerificationRepository,
    PermissionRepository,
    RoleRepository,
    TenantRepository,
    ThemeRepository,
    UserFieldRepository,
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
)
from fief.schemas.user import UserCreateAdmin
from fief.services.admin import (
    ADMIN_PERMISSION_CODENAME,
    ADMIN_PERMISSION_NAME,
    ADMIN_ROLE_NAME,
)
from fief.services.email_template.initializer import EmailTemplateInitializer
from fief.services.user_roles import UserRolesService
from fief.services.webhooks.trigger import trigger_webhooks
from fief.tasks import send_task

if TYPE_CHECKING:
    from fief.settings import Settings


class InitializerError(Exception):
    pass


class DefaultTenantDoesNotExist(InitializerError):
    pass


class AdminAPIKeyAlreadyExists(InitializerError):
    pass


class UserDoesNotExist(InitializerError):
    pass


class Initializer:
    def __init__(self, engine: AsyncEngine, settings: "Settings") -> None:
        self.engine = engine
        self.sessionmaker = create_main_async_session_maker(engine)
        self.settings = settings

    async def init_all(self) -> None:
        async with self.sessionmaker() as session:
            await self._init_default_tenant(session)
            await self._init_admin_role(session)
            await self._init_default_theme(session)
            await self._init_email_templates(session)

    async def create_admin(self, email: str, password: str | None = None) -> User:
        async with self.sessionmaker() as session:
            await self._init_admin_role(session)

            tenant_repository = TenantRepository(session)
            tenant = await tenant_repository.get_default()

            if tenant is None:
                raise DefaultTenantDoesNotExist()

            user_repository = UserRepository(session)
            email_verification_repository = EmailVerificationRepository(session)
            user_fields = await UserFieldRepository(session).all()
            audit_logger = await get_audit_logger(None, None)
            trigger_webhooks_partial = functools.partial(
                trigger_webhooks, send_task=send_task
            )

            user_roles_service = UserRolesService(
                UserRoleRepository(session),
                UserPermissionRepository(session),
                RoleRepository(session),
                audit_logger,
                trigger_webhooks_partial,
                send_task,
            )
            user_manager = await get_user_manager(
                user_repository,
                email_verification_repository,
                user_fields,
                send_task,
                audit_logger,
                trigger_webhooks_partial,
                user_roles_service,
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

            role_repository = RoleRepository(session)
            admin_role = await role_repository.get_by_name(ADMIN_ROLE_NAME)
            if admin_role is not None:
                await user_roles_service.add_role(user, admin_role, run_in_worker=False)

        return user

    async def create_admin_api_key(self, token: str) -> AdminAPIKey:
        async with self.sessionmaker() as session:
            admin_api_key_repository = AdminAPIKeyRepository(session)

            token_hash = get_token_hash(token)
            admin_api_key = await admin_api_key_repository.get_by_token(token_hash)

            if admin_api_key is not None:
                raise AdminAPIKeyAlreadyExists()

            admin_api_key = AdminAPIKey(
                name="Environment variable key", token=token_hash
            )
            await admin_api_key_repository.create(admin_api_key)

        return admin_api_key

    async def grant_admin_role(self, email: str) -> User:
        async with self.sessionmaker() as session:
            await self._init_admin_role(session)

            tenant_repository = TenantRepository(session)
            tenant = await tenant_repository.get_default()

            if tenant is None:
                raise DefaultTenantDoesNotExist()

            user_repository = UserRepository(session)
            audit_logger = await get_audit_logger(None, None)
            trigger_webhooks_partial = functools.partial(
                trigger_webhooks, send_task=send_task
            )
            user_roles_service = UserRolesService(
                UserRoleRepository(session),
                UserPermissionRepository(session),
                RoleRepository(session),
                audit_logger,
                trigger_webhooks_partial,
                send_task,
            )

            user = await user_repository.get_by_email_and_tenant(email, tenant.id)

            if user is None:
                raise UserDoesNotExist()

            role_repository = RoleRepository(session)
            admin_role = await role_repository.get_by_name(ADMIN_ROLE_NAME)
            if admin_role is not None:
                await user_roles_service.add_role(user, admin_role, run_in_worker=False)

        return user

    async def _init_default_tenant(self, session: AsyncSession) -> Tenant:
        repository = TenantRepository(session)

        tenant = await repository.get_default()
        if tenant is None:
            tenant_name = "Default"
            tenant_slug = await repository.get_available_slug(tenant_name)
            tenant = Tenant(name=tenant_name, slug=tenant_slug, default=True)
            tenant = await repository.create(tenant)

        await self._init_default_client(session, tenant)

        return tenant

    async def _init_default_client(
        self, session: AsyncSession, tenant: Tenant
    ) -> Client:
        repository = ClientRepository(session)

        client_id = self.settings.fief_client_id
        redirect_uris = [
            f"http://{self.settings.fief_domain}/admin/auth/callback",
            f"https://{self.settings.fief_domain}/admin/auth/callback",
            f"http://{self.settings.fief_domain}/docs/oauth2-redirect",
            f"https://{self.settings.fief_domain}/docs/oauth2-redirect",
        ]

        client = await repository.get_by_client_id(client_id)
        if client is not None:
            for redirect_uri in redirect_uris:
                if redirect_uri not in client.redirect_uris:
                    client.redirect_uris.append(redirect_uri)
            await repository.update(client)
            return client

        client = Client(
            name=f"{tenant.name}'s client",
            first_party=True,
            tenant=tenant,
            redirect_uris=redirect_uris,
        )

        client.client_id = client_id
        client.client_secret = self.settings.fief_client_secret
        if self.settings.fief_encryption_key is not None:
            client.encrypt_jwk = self.settings.fief_encryption_key

        return await repository.create(client)

    async def _init_admin_role(self, session: AsyncSession) -> None:
        role_repository = RoleRepository(session)
        permission_repository = PermissionRepository(session)

        permission = await permission_repository.get_by_codename(
            ADMIN_PERMISSION_CODENAME
        )
        if permission is None:
            permission = await permission_repository.create(
                Permission(
                    name=ADMIN_PERMISSION_NAME, codename=ADMIN_PERMISSION_CODENAME
                )
            )
            await role_repository.create(
                Role(
                    name=ADMIN_ROLE_NAME, permissions=[permission], user_permissions=[]
                )
            )

    async def _init_default_theme(self, session: AsyncSession) -> None:
        repository = ThemeRepository(session)
        default_theme = await repository.get_default()
        if default_theme is None:
            await repository.create(Theme.build_default())

    async def _init_email_templates(self, session: AsyncSession) -> None:
        email_template_repository = EmailTemplateRepository(session)
        email_template_initializer = EmailTemplateInitializer(email_template_repository)
        await email_template_initializer.init_templates()
