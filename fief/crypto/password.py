from fastapi_users.password import PasswordHelper as BasePasswordHelper
from passlib import pwd
from passlib.context import CryptContext

context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


class PasswordHelper(BasePasswordHelper):
    def generate(self) -> str:
        return pwd.genword(entropy=128)


password_helper = PasswordHelper(context)
