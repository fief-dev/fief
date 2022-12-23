import binascii

from cryptography.fernet import Fernet
from sqlalchemy import Text
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    FernetEngine as BaseFernetEngine,
)
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    StringEncryptedType as BaseStringEncryptedType,
)


class StringEncryptedType(BaseStringEncryptedType):
    impl = Text


def generate_key() -> bytes:
    return Fernet.generate_key()


def is_valid_key(key: bytes) -> bool:
    try:
        Fernet(key)
    except binascii.Error:
        return False
    else:
        return True


class FernetEngine(BaseFernetEngine):
    """
    Overload of the built-in SQLAlchemy Utils Fernet engine.

    For unknown reasons, they hash the encryption key before using it.

    For backward compatibility, we adjust the implementation to use the key as provided.
    """

    def _update_key(self, key: bytes):
        return self._initialize_engine(key)

    def _initialize_engine(self, parent_class_key: bytes):
        self.secret_key = parent_class_key
        self.fernet = Fernet(self.secret_key)
