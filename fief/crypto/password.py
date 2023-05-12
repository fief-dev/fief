from fastapi_users.password import PasswordHelper as BasePasswordHelper
from passlib.context import CryptContext
from passlib import pwd

context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


class PasswordHelper(BasePasswordHelper):
    def generate(self) -> str:
        return pwd.genword(entropy=128)


password_helper = PasswordHelper(context)
