from typing import Optional

from pydantic import UUID4

from fief.db.account import get_account_session
from fief.db.main import main_async_session_maker
from fief.dependencies.users import get_user_db, get_user_manager
from fief.locale import get_preferred_translations
from fief.managers import AccountManager, AccountUserManager, TenantManager
from fief.models import Account, AccountUser, Client, Tenant
from fief.schemas.account import AccountCreate
from fief.schemas.user import UserCreateInternal, UserDB
from fief.services.account_db import AccountDatabase
from fief.settings import settings
from fief.tasks import send_task


class AccountCreation:
    def __init__(
        self,
        account_manager: AccountManager,
        account_user_manager: AccountUserManager,
        account_db: AccountDatabase,
    ) -> None:
        self.account_manager = account_manager
        self.account_user_manager = account_user_manager
        self.account_db = account_db

    async def create(
        self,
        account_create: AccountCreate,
        user_id: Optional[UUID4] = None,
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

        # Link the user to this account
        if user_id is not None:
            account_user = AccountUser(account_id=account.id, user_id=user_id)
            await self.account_user_manager.create(account_user)

        # Create a default tenant and client
        async with get_account_session(account) as session:
            tenant_name = account.name
            tenant_slug = await TenantManager(session).get_available_slug(tenant_name)
            tenant = Tenant(name=account.name, slug=tenant_slug, default=True)

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

        return account


class MainAccountAlreadyExists(Exception):
    pass


async def create_main_fief_account() -> Account:
    async with main_async_session_maker() as session:
        account_manager = AccountManager(session)
        account_user_manager = AccountUserManager(session)
        account = await account_manager.get_by_domain(settings.fief_domain)

        if account is not None:
            raise MainAccountAlreadyExists()

        account_create = AccountCreate(name="Fief")
        account_db = AccountDatabase()
        account_creation = AccountCreation(
            account_manager, account_user_manager, account_db
        )

        account = await account_creation.create(
            account_create,
            default_domain=settings.fief_domain,
            default_client_id=settings.fief_client_id,
            default_client_secret=settings.fief_client_secret,
            default_encryption_key=settings.fief_encryption_key,
        )

    return account


class CreateMainFiefUserError(Exception):
    pass


class MainAccountDoesNotExist(Exception):
    pass


class MainAccountDoesNotHaveDefaultTenant(Exception):
    pass


async def create_main_fief_user(email: str, password: str) -> UserDB:
    async with main_async_session_maker() as session:
        account_manager = AccountManager(session)
        account_user_manager = AccountUserManager(session)
        account = await account_manager.get_by_domain(settings.fief_domain)

        if account is None:
            raise MainAccountDoesNotExist()

        async with get_account_session(account) as session:
            tenant_manager = TenantManager(session)
            tenant = await tenant_manager.get_default()

            if tenant is None:
                raise MainAccountDoesNotHaveDefaultTenant()

            user_db = await get_user_db(session, tenant)
            user_manager = await get_user_manager(
                user_db, tenant, account, get_preferred_translations(["en"]), send_task
            )
            user = await user_manager.create(UserCreateInternal(email=email, password=password, tenant_id=tenant.id))

        account_user = AccountUser(account_id=account.id, user_id=user.id)
        await account_user_manager.create(account_user)

    return user
