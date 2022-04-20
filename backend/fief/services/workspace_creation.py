import re
from typing import List, Optional

from pydantic import UUID4

from fief.db.workspace import get_workspace_session
from fief.managers import (
    ClientManager,
    TenantManager,
    WorkspaceManager,
    WorkspaceUserManager,
)
from fief.models import Client, Tenant, Workspace, WorkspaceUser
from fief.schemas.workspace import WorkspaceCreate
from fief.services.main_workspace import get_main_fief_client, get_main_fief_workspace
from fief.services.workspace_db import WorkspaceDatabase

LOCALHOST_HOST_PATTERN = re.compile(r"([^\.]+\.)?localhost(\d+)?", flags=re.IGNORECASE)


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
        default_redirect_uris: Optional[List[str]] = None,
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
        alembic_revision = self.workspace_db.migrate(
            workspace.get_database_url(False), workspace.get_schema_name()
        )
        workspace.alembic_revision = alembic_revision
        await self.workspace_manager.update(workspace)

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

            await session.commit()

        # Allow a redirect URI on this workspace on the main Fief client
        await self._add_fief_redirect_uri(workspace)

        return workspace

    async def _add_fief_redirect_uri(self, workspace: Workspace):
        main_workspace = await get_main_fief_workspace()

        async with get_workspace_session(main_workspace) as session:
            client_manager = ClientManager(session)
            fief_client = await get_main_fief_client()

            localhost_domain = LOCALHOST_HOST_PATTERN.match(workspace.domain)
            redirect_uri = f"{'http' if localhost_domain else 'https'}://{workspace.domain}/admin/api/auth/callback"
            fief_client.redirect_uris = fief_client.redirect_uris + [redirect_uri]

            await client_manager.update(fief_client)
