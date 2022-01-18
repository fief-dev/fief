from fief.db import get_account_session
from fief.managers import AccountManager
from fief.models import Account, Client, Tenant
from fief.schemas.account import AccountCreate
from fief.services.account_db import AccountDatabase


class AccountCreation:
    def __init__(
        self, account_manager: AccountManager, account_db: AccountDatabase
    ) -> None:
        self.account_manager = account_manager
        self.account_db = account_db

    async def create(self, account_create: AccountCreate) -> Account:
        # Create account on available subdomain
        account = Account(**account_create.dict())
        domain = await self.account_manager.get_available_subdomain(account.name)
        account.domain = domain
        account = await self.account_manager.create(account)

        # Apply the database schema
        self.account_db.migrate(account)

        # Create a default tenant and client
        async with get_account_session(account) as session:
            tenant = Tenant(name=account.name, default=True)
            session.add(tenant)

            client = Client(name=f"{tenant.name}'s client", tenant=tenant)
            session.add(client)

            await session.commit()

        return account
