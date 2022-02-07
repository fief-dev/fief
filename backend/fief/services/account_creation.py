from typing import Optional

from fief.db import get_account_session, global_async_session_maker
from fief.logging import logger
from fief.managers import AccountManager, TenantManager
from fief.models import Account, Client, Tenant
from fief.schemas.account import AccountCreate
from fief.services.account_db import AccountDatabase
from fief.settings import settings


class AccountCreation:
    def __init__(
        self, account_manager: AccountManager, account_db: AccountDatabase
    ) -> None:
        self.account_manager = account_manager
        self.account_db = account_db

    async def create(
        self,
        account_create: AccountCreate,
        default_domain: Optional[str] = None,
        default_client_id: Optional[str] = None,
        default_client_secret: Optional[str] = None,
        default_encryption_key: Optional[str] = None,
    ) -> Account:
        account = Account(**account_create.dict())

        if default_domain is None:
            # Create account on available subdomain
            domain = await self.account_manager.get_available_subdomain(account.name)
            account.domain = domain
        else:
            account.domain = default_domain

        account = await self.account_manager.create(account)

        # Apply the database schema
        self.account_db.migrate(
            account.get_database_url(False), account.get_schema_name()
        )

        # Create a default tenant and client
        async with get_account_session(account) as session:
            tenant_name = account.name
            tenant_slug = await TenantManager(session).get_available_slug(tenant_name)
            tenant = Tenant(name=account.name, slug=tenant_slug, default=True)

            if default_encryption_key is not None:
                tenant.encrypt_jwk = default_encryption_key

            session.add(tenant)

            client = Client(name=f"{tenant.name}'s client", tenant=tenant)

            if default_client_id is not None:
                client.client_id = default_client_id
            if default_client_secret is not None:
                client.client_secret = default_client_secret

            session.add(client)

            await session.commit()

        return account


async def create_global_fief_account():
    async with global_async_session_maker() as session:
        account_manager = AccountManager(session)
        account = await account_manager.get_by_domain(settings.fief_domain)

        if account is not None:
            logger.debug(f"Global Fief account {account.domain} already exists")
            return

        account_create = AccountCreate(name="Fief")
        account_db = AccountDatabase()
        account_creation = AccountCreation(account_manager, account_db)

        account = await account_creation.create(
            account_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
        )

    logger.info(f"Global Fief account {account.domain} created")
