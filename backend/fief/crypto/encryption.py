import binascii

from cryptography import fernet


def is_valid_key(key: bytes) -> bool:
    try:
        fernet.Fernet(key)
    except binascii.Error:
        return False
    else:
        return True


def encrypt(value: str, key: bytes) -> str:
    f = fernet.Fernet(key)
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str, key: bytes) -> str:
    f = fernet.Fernet(key)
    return f.decrypt(value.encode("utf-8")).decode("utf-8")
