from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport

from fief.dependencies.users import get_database_strategy, get_user_manager
from fief.schemas import user

bearer_token_backend = AuthenticationBackend(
    name="token",
    transport=BearerTransport("/auth/token/login"),
    get_strategy=get_database_strategy,
)

fastapi_users = FastAPIUsers(
    get_user_manager,
    [bearer_token_backend],
    user.User,
    user.UserCreate,
    user.UserUpdate,
    user.UserDB,
)
