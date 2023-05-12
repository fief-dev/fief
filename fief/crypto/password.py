from passlib import pwd
from passlib.context import CryptContext


class PasswordHelper:
    def __init__(self) -> None:
        self.context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def verify_and_update(
        self, plain_password: str, hashed_password: str
    ) -> tuple[bool, str]:
        return self.context.verify_and_update(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return self.context.hash(password)

    def generate(self) -> str:
        return pwd.genword(entropy=128)


password_helper = PasswordHelper()
