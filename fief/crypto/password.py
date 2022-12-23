from fastapi_users.password import PasswordHelper
from passlib.context import CryptContext

context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
password_helper = PasswordHelper(context)
