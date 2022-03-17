from typing import Optional

from pydantic import UUID4

from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.dependencies.users import get_user_db, get_user_manager
from fief.locale import get_preferred_translations
from fief.managers import TenantManager, WorkspaceManager, WorkspaceUserManager
from fief.models import Client, Tenant, Workspace, WorkspaceUser
from fief.schemas.user import UserCreateInternal, UserDB
from fief.schemas.workspace import WorkspaceCreate
from fief.services.workspace_db import WorkspaceDatabase
from fief.settings import settings
from fief.tasks import send_task


class WorkspaceCreation:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        workspace_user_manager: WorkspaceUserManager,
        workspace_db: WorkspaceDatabase,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.workspace_user_manager = workspace_user_manager
        self.workspace_db = workspace_db

    async def create(
        self,
        workspace_create: WorkspaceCreate,
        user_id: Optional[UUID4] = None,
        default_domain: Optional[str] = None,
        default_client_id: Optional[str] = None,
        default_client_secret: Optional[str] = None,
        default_encryption_key: Optional[str] = None,
    ) -> Workspace:
        workspace = Workspace(**workspace_create.dict())

        if default_domain is None:
            # Create workspace on available subdomain
            domain = await self.workspace_manager.get_available_subdomain(
                workspace.name
            )
            workspace.domain = domain
        else:
            workspace.domain = default_domain

        workspace = await self.workspace_manager.create(workspace)

        # Apply the database schema
        self.workspace_db.migrate(
            workspace.get_database_url(False), workspace.get_schema_name()
        )

        # Link the user to this workspace
        if user_id is not None:
            workspace_user = WorkspaceUser(workspace_id=workspace.id, user_id=user_id)
            await self.workspace_user_manager.create(workspace_user)

        # Create a default tenant and client
        async with get_workspace_session(workspace) as session:
            tenant_name = workspace.name
            tenant_slug = await TenantManager(session).get_available_slug(tenant_name)
            tenant = Tenant(name=workspace.name, slug=tenant_slug, default=True)

            session.add(tenant)

            client = Client(
                name=f"{tenant.name}'s client", first_party=True, tenant=tenant
            )

            if default_client_id is not None:
                client.client_id = default_client_id
            if default_client_secret is not None:
                client.client_secret = default_client_secret
            if default_encryption_key is not None:
                client.encrypt_jwk = default_encryption_key

            session.add(client)

            await session.commit()

        return workspace


class MainWorkspaceAlreadyExists(Exception):
    pass


async def create_main_fief_workspace() -> Workspace:
    async with main_async_session_maker() as session:
        workspace_manager = WorkspaceManager(session)
        workspace_user_manager = WorkspaceUserManager(session)
        workspace = await workspace_manager.get_by_domain(settings.fief_domain)

        if workspace is not None:
            raise MainWorkspaceAlreadyExists()

        workspace_create = WorkspaceCreate(name="Fief")
        workspace_db = WorkspaceDatabase()
        workspace_creation = WorkspaceCreation(
            workspace_manager, workspace_user_manager, workspace_db
        )

        workspace = await workspace_creation.create(
            workspace_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
        )

    return workspace


class CreateMainFiefUserError(Exception):
    pass


class MainWorkspaceDoesNotExist(Exception):
    pass


class MainWorkspaceDoesNotHaveDefaultTenant(Exception):
    pass


async def create_main_fief_user(email: str, password: str) -> UserDB:
    async with main_async_session_maker() as session:
        workspace_manager = WorkspaceManager(session)
        workspace_user_manager = WorkspaceUserManager(session)
        workspace = await workspace_manager.get_by_domain(settings.fief_domain)

        if workspace is None:
            raise MainWorkspaceDoesNotExist()

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
