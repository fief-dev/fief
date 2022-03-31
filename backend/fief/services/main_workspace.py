from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.dependencies.users import get_user_db, get_user_manager
from fief.locale import get_preferred_translations
from fief.managers import (
    ClientManager,
    TenantManager,
    WorkspaceManager,
    WorkspaceUserManager,
)
from fief.models import Client, Workspace, WorkspaceUser
from fief.schemas.user import UserCreateInternal, UserDB
from fief.schemas.workspace import WorkspaceCreate
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


async def get_main_fief_workspace() -> Workspace:
    async with main_async_session_maker() as session:
        workspace_manager = WorkspaceManager(session)
        workspace = await workspace_manager.get_main()

        if workspace is None:
            raise MainWorkspaceDoesNotExist()

        return workspace


async def get_main_fief_client() -> Client:
    workspace = await get_main_fief_workspace()
    async with get_workspace_session(workspace) as session:
        client_manager = ClientManager(session)
        client = await client_manager.get_by_client_id(settings.fief_client_id)

        if client is None:
            raise MainWorkspaceClientDoesNotExist()

        return client


async def create_main_fief_workspace() -> Workspace:
    from fief.services.workspace_creation import WorkspaceCreation

    async with main_async_session_maker() as session:
        workspace_manager = WorkspaceManager(session)
        workspace_user_manager = WorkspaceUserManager(session)
        workspace = await workspace_manager.get_main()

        if workspace is not None:
            raise MainWorkspaceAlreadyExists()

        workspace_create = WorkspaceCreate(name="Fief")
        workspace_db = WorkspaceDatabase()
        workspace_creation = WorkspaceCreation(
            workspace_manager, workspace_user_manager, workspace_db
        )

        localhost_domain = settings.fief_domain.endswith("localhost")
        default_redirect_uri = f"{'http' if localhost_domain else 'https'}://{settings.fief_domain}/admin/api/auth/callback"
        workspace = await workspace_creation.create(
            workspace_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
            default_redirect_uris=[
                default_redirect_uri,
                "http://localhost:8000/docs/oauth2-redirect",
            ],
        )

    return workspace


async def create_main_fief_user(email: str, password: str) -> UserDB:
    workspace = await get_main_fief_workspace()

    async with main_async_session_maker() as session:
        workspace_user_manager = WorkspaceUserManager(session)

        async with get_workspace_session(workspace) as session:
            tenant_manager = TenantManager(session)
            tenant = await tenant_manager.get_default()

            if tenant is None:
                raise MainWorkspaceDoesNotHaveDefaultTenant()

            user_db = await get_user_db(session, tenant)
            user_manager = await get_user_manager(
                user_db,
                tenant,
                workspace,
                get_preferred_translations(["en"]),
                send_task,
            )
            user = await user_manager.create(
                UserCreateInternal(email=email, password=password, tenant_id=tenant.id)
            )

        workspace_user = WorkspaceUser(workspace_id=workspace.id, user_id=user.id)
        await workspace_user_manager.create(workspace_user)

    return user
