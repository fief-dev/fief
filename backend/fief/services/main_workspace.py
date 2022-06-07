from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.dependencies.users import get_user_db, get_user_manager
from fief.locale import get_preferred_translations
from fief.models import Client, User, Workspace, WorkspaceUser
from fief.repositories import (
    ClientRepository,
    TenantRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from fief.schemas.user import UserCreateInternal
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
        workspace_repository = WorkspaceRepository(session)
        workspace = await workspace_repository.get_main()

        if workspace is None:
            raise MainWorkspaceDoesNotExist()

        return workspace


async def get_main_fief_client() -> Client:
    workspace = await get_main_fief_workspace()
    async with get_workspace_session(workspace) as session:
        client_repository = ClientRepository(session)
        client = await client_repository.get_by_client_id(settings.fief_client_id)

        if client is None:
            raise MainWorkspaceClientDoesNotExist()

        return client


async def create_main_fief_workspace() -> Workspace:
    from fief.services.workspace_creation import WorkspaceCreation

    async with main_async_session_maker() as session:
        workspace_repository = WorkspaceRepository(session)
        workspace_user_repository = WorkspaceUserRepository(session)
        workspace = await workspace_repository.get_main()

        if workspace is not None:
            raise MainWorkspaceAlreadyExists()

        workspace_create = WorkspaceCreate(name="Fief")
        workspace_db = WorkspaceDatabase()
        workspace_creation = WorkspaceCreation(
            workspace_repository, workspace_user_repository, workspace_db
        )

        workspace = await workspace_creation.create(
            workspace_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
            default_redirect_uris=[
                f"http://{settings.fief_domain}/admin/api/auth/callback",
                f"https://{settings.fief_domain}/admin/api/auth/callback",
                "http://localhost:8000/docs/oauth2-redirect",
            ],
        )

    return workspace


async def create_main_fief_user(email: str, password: str) -> User:
    workspace = await get_main_fief_workspace()

    async with main_async_session_maker() as session:
        workspace_user_repository = WorkspaceUserRepository(session)

        async with get_workspace_session(workspace) as session:
            tenant_repository = TenantRepository(session)
            tenant = await tenant_repository.get_default()

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
        await workspace_user_repository.create(workspace_user)

    return user
