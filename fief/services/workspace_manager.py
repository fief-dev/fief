from posthog import Posthog
from pydantic import UUID4

from fief.db.main import get_single_main_async_session
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.models import Client, Tenant, Workspace, WorkspaceUser
from fief.repositories import (
    ClientRepository,
    EmailTemplateRepository,
    TenantRepository,
    ThemeRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from fief.schemas.workspace import WorkspaceCreate
from fief.services.email_template.initializer import EmailTemplateInitializer
from fief.services.localhost import is_localhost
from fief.services.main_workspace import get_main_fief_client, get_main_fief_workspace
from fief.services.posthog import get_server_id, posthog
from fief.services.theme import init_default_theme
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)


class WorkspaceManager:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_user_repository: WorkspaceUserRepository,
        workspace_db: WorkspaceDatabase,
        workspace_engine_manager: WorkspaceEngineManager,
        posthog: Posthog,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.workspace_user_repository = workspace_user_repository
        self.workspace_db = workspace_db
        self.workspace_engine_manager = workspace_engine_manager
        self.posthog = posthog

    async def create(
        self,
        workspace_create: WorkspaceCreate,
        user_id: UUID4 | None = None,
        default_domain: str | None = None,
        default_client_id: str | None = None,
        default_client_secret: str | None = None,
        default_redirect_uris: list[str] | None = None,
        default_encryption_key: str | None = None,
    ) -> Workspace:
        workspace = Workspace(**workspace_create.dict())

        if default_domain is None:
            # Create workspace on available subdomain
            domain = await self.workspace_repository.get_available_subdomain(
                workspace.name
            )
            workspace.domain = domain
        else:
            workspace.domain = default_domain

        workspace = await self.workspace_repository.create(workspace)

        # Apply the database schema
        try:
            alembic_revision = self.workspace_db.migrate(
                workspace.get_database_connection_parameters(False),
                workspace.get_schema_name(),
            )
        except WorkspaceDatabaseConnectionError:
            await self.workspace_repository.delete(workspace)
            raise

        workspace.alembic_revision = alembic_revision
        await self.workspace_repository.update(workspace)

        # Link the user to this workspace
        if user_id is not None:
            workspace_user = WorkspaceUser(workspace_id=workspace.id, user_id=user_id)
            await self.workspace_user_repository.create(workspace_user)

        # Create a default tenant, client and email templates
        async with get_workspace_session(
            workspace, self.workspace_engine_manager
        ) as session:
            tenant_name = workspace.name
            tenant_slug = await TenantRepository(session).get_available_slug(
                tenant_name
            )
            tenant = Tenant(name=workspace.name, slug=tenant_slug, default=True)

            session.add(tenant)

            client = Client(
                name=f"{tenant.name}'s client",
                first_party=True,
                tenant=tenant,
                redirect_uris=default_redirect_uris
                if default_redirect_uris is not None
                else ["http://localhost:8000/docs/oauth2-redirect"],
            )

            if default_client_id is not None:
                client.client_id = default_client_id
            if default_client_secret is not None:
                client.client_secret = default_client_secret
            if default_encryption_key is not None:
                client.encrypt_jwk = default_encryption_key

            session.add(client)

            email_template_repository = EmailTemplateRepository(session)
            email_template_initializer = EmailTemplateInitializer(
                email_template_repository
            )
            await email_template_initializer.init_templates()

            theme_repository = ThemeRepository(session)
            await init_default_theme(theme_repository)

            await session.commit()

        # Allow a redirect URI on this workspace on the main Fief client
        await self._add_fief_redirect_uri(workspace)

        # Inform telemetry
        event_user_id = str(user_id) if user_id is not None else get_server_id()
        self.posthog.capture(
            event_user_id,
            "Workspace Created",
            groups={"server": get_server_id(), "workspace": str(workspace.id)},
        )

        return workspace

    async def delete(self, workspace: Workspace, user_id: UUID4 | None = None) -> None:
        # Delete cloud data. Keep data on BYOD untouched.
        if workspace.database_type is None:
            self.workspace_db.drop(
                workspace.get_database_connection_parameters(False),
                workspace.get_schema_name(),
            )

        await self.workspace_repository.delete(workspace)

        # Inform telemetry
        event_user_id = str(user_id) if user_id is not None else get_server_id()
        self.posthog.capture(
            event_user_id,
            "Workspace Deleted",
            groups={"server": get_server_id(), "workspace": str(workspace.id)},
        )

    async def _add_fief_redirect_uri(self, workspace: Workspace):
        main_workspace = await get_main_fief_workspace()

        async with get_workspace_session(
            main_workspace, self.workspace_engine_manager
        ) as session:
            client_repository = ClientRepository(session)
            fief_client = await get_main_fief_client()

            is_localhost_domain = is_localhost(workspace.domain)
            redirect_uri = f"{'http' if is_localhost_domain else 'https'}://{workspace.domain}/admin/auth/callback"
            fief_client.redirect_uris = fief_client.redirect_uris + [redirect_uri]

            await client_repository.update(fief_client)


class WorkspaceDoesNotExistError(Exception):
    pass


async def delete_workspace_by_domain(domain: str) -> None:
    async with get_single_main_async_session() as session:
        workspace_repository = WorkspaceRepository(session)
        workspace_user_repository = WorkspaceUserRepository(session)
        workspace_db = WorkspaceDatabase()

        workspace = await workspace_repository.get_by_domain(domain)
        if workspace is None:
            raise WorkspaceDoesNotExistError()

        async with WorkspaceEngineManager() as workspace_engine_manager:
            workspace_manager = WorkspaceManager(
                workspace_repository,
                workspace_user_repository,
                workspace_db,
                workspace_engine_manager,
                posthog,
            )
            await workspace_manager.delete(workspace)
