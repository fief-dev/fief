from typing import AsyncGenerator, Optional, Type, cast

from fastapi import Depends, Request
from fastapi_users import BaseUserManager
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseOAuthAccountTable,
    SQLAlchemyBaseUserTable,
    SQLAlchemyUserDatabase,
)
from sqlalchemy.sql import Select

from fief.db import AsyncSession
from fief.dependencies.account import get_current_account_session
from fief.dependencies.tenant import get_current_tenant
from fief.models import Tenant, User
from fief.schemas.user import UserCreate, UserCreateInternal, UserDB


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = "SECRET"
    verification_token_secret = "SECRET"

    def __init__(self, user_db: SQLAlchemyUserDatabase[UserDB], tenant: Tenant):
        super().__init__(user_db)
        self.tenant = tenant

    async def create(
        self, user: UserCreate, safe: bool = False, request: Optional[Request] = None
    ) -> UserDB:
        user_dict = (
            user.create_update_dict() if safe else user.create_update_dict_superuser()
        )
        user_create = UserCreateInternal(**user_dict, tenant_id=self.tenant.id)
        return await super().create(user_create, safe=safe, request=request)

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


class SQLAlchemyUserTenantDatabase(SQLAlchemyUserDatabase[UserDB]):
    def __init__(
        self,
        user_db_model: Type[UserDB],
        session: AsyncSession,
        tenant: Tenant,
        user_table: Type[User],
        oauth_account_table: Optional[Type[SQLAlchemyBaseOAuthAccountTable]] = None,
    ):
        super().__init__(
            user_db_model,
            session,
            cast(Type[SQLAlchemyBaseUserTable], user_table),
            oauth_account_table=oauth_account_table,
        )
        self.tenant = tenant

    async def _get_user(self, statement: Select) -> Optional[UserDB]:
        statement = statement.where(User.tenant_id == self.tenant.id)
        return await super()._get_user(statement)


async def get_user_db(
    session: AsyncSession = Depends(get_current_account_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> AsyncGenerator[SQLAlchemyUserDatabase[UserDB], None]:
    yield SQLAlchemyUserTenantDatabase(UserDB, session, tenant, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[UserDB] = Depends(get_user_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    yield UserManager(user_db, tenant)
