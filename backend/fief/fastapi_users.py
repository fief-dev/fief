from fastapi_users import FastAPIUsers

from fief.dependencies.users import get_user_manager
from fief.schemas import user

fastapi_users = FastAPIUsers(
    get_user_manager, [], user.User, user.UserCreate, user.UserUpdate, user.UserDB
)
