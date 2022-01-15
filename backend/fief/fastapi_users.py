from fastapi_users import FastAPIUsers

from fief.dependencies.users import authentication_backend, get_user_manager
from fief.schemas import user

fastapi_users = FastAPIUsers(
    get_user_manager,
    [authentication_backend],
    user.User,
    user.UserCreate,
    user.UserUpdate,
    user.UserDB,
)

current_active_user = fastapi_users.current_user(active=True)
