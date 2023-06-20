import functools

from fief.crypto.token import get_token_hash
from fief.db.main import create_main_async_session_maker
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.users import get_user_manager
from fief.models import AdminAPIKey, Client, User, Workspace, WorkspaceUser
from fief.repositories import (
    AdminAPIKeyRepository,
    ClientRepository,
    EmailVerificationRepository,
    TenantRepository,
    UserFieldRepository,
    UserRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from fief.schemas.user import UserCreateAdmin
from fief.schemas.workspace import WorkspaceCreate
from fief.services.posthog import posthog
from fief.services.webhooks.trigger import trigger_webhooks
from fief.services.workspace_db import WorkspaceDatabase
from fief.settings import settings
from fief.tasks import send_task


class MainWorkspaceError(Exception):
    pass


class MainWorkspaceAlreadyExists(MainWorkspaceError):
    pass


class MainWorkspaceDoesNotExist(MainWorkspaceError):
    pass


class MainWorkspaceDoesNotHaveDefaultTenant(MainWorkspaceError):
    pass


class MainWorkspaceClientDoesNotExist(MainWorkspaceError):
    pass


class CreateMainFiefUserError(MainWorkspaceError):
    pass


class MainFiefAdminApiKeyAlreadyExists(MainWorkspaceError):
    pass


async def get_main_fief_workspace() -> Workspace:
    main_async_session_maker = create_main_async_session_maker()
    async with main_async_session_maker() as session:
        workspace_repository = WorkspaceRepository(session)
        workspace = await workspace_repository.get_main()

        if workspace is None:
            raise MainWorkspaceDoesNotExist()

        return workspace


async def get_main_fief_client() -> Client:
    workspace = await get_main_fief_workspace()
    async with get_workspace_session(workspace, WorkspaceEngineManager()) as session:
        client_repository = ClientRepository(session)
        client = await client_repository.get_by_client_id(settings.fief_client_id)

        if client is None:
            raise MainWorkspaceClientDoesNotExist()

        return client


async def create_main_fief_workspace() -> Workspace:
    from fief.services.workspace_creation import WorkspaceCreation

    main_async_session_maker = create_main_async_session_maker()
    workspace_engine_manager = WorkspaceEngineManager()

    async with main_async_session_maker() as session:
        workspace_repository = WorkspaceRepository(session)
        workspace_user_repository = WorkspaceUserRepository(session)
        workspace = await workspace_repository.get_main()

        if workspace is not None:
            raise MainWorkspaceAlreadyExists()

        workspace_create = WorkspaceCreate(name="Fief")
        workspace_db = WorkspaceDatabase()
        workspace_creation = WorkspaceCreation(
            workspace_repository,
            workspace_user_repository,
            workspace_db,
            workspace_engine_manager,
            posthog,
        )

        workspace = await workspace_creation.create(
            workspace_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
            default_redirect_uris=[
                f"http://{settings.fief_domain}/admin/auth/callback",
                f"https://{settings.fief_domain}/admin/auth/callback",
                "http://localhost:8000/docs/oauth2-redirect",
            ],
        )

    return workspace


async def create_main_fief_user(email: str, password: str | None = None) -> User:
    workspace = await get_main_fief_workspace()
    main_async_session_maker = create_main_async_session_maker()
    async with main_async_session_maker() as session:
        workspace_user_repository = WorkspaceUserRepository(session)

        async with get_workspace_session(
            workspace, WorkspaceEngineManager()
        ) as session:
            tenant_repository = TenantRepository(session)
            tenant = await tenant_repository.get_default()

            if tenant is None:
                raise MainWorkspaceDoesNotHaveDefaultTenant()

            user_repository = UserRepository(session)
            email_verification_repository = EmailVerificationRepository(session)
            user_fields = await UserFieldRepository(session).all()
            audit_logger = await get_audit_logger(workspace, None, None)

            user_manager = await get_user_manager(
                workspace,
                user_repository,
                email_verification_repository,
                user_fields,
                send_task,
                audit_logger,
                functools.partial(
                    trigger_webhooks, workspace_id=workspace.id, send_task=send_task
                ),
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

        workspace_user = WorkspaceUser(workspace_id=workspace.id, user_id=user.id)
        await workspace_user_repository.create(workspace_user)

    return user


async def create_main_fief_admin_api_key(token: str) -> AdminAPIKey:
    workspace = await get_main_fief_workspace()
    main_async_session_maker = create_main_async_session_maker()
    async with main_async_session_maker() as session:
        admin_api_key_repository = AdminAPIKeyRepository(session)

        token_hash = get_token_hash(token)
        admin_api_key = await admin_api_key_repository.get_by_token(token_hash)

        if admin_api_key is not None:
            raise MainFiefAdminApiKeyAlreadyExists()

        async with get_workspace_session(
            workspace, WorkspaceEngineManager()
        ) as session:
            admin_api_key = AdminAPIKey(
                name="Environment variable key",
                token=token_hash,
                workspace_id=workspace.id,
            )
            await admin_api_key_repository.create(admin_api_key)

    return admin_api_key
