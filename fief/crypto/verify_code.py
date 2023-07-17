import hashlib
import hmac
import secrets
import string

from fief.settings import settings


def get_verify_code_hash(
    code: str, *, secret: str = settings.secret.get_secret_value()
) -> str:
    hash = hmac.new(secret.encode("ascii"), code.encode("ascii"), hashlib.sha256)
    return hash.hexdigest()


def generate_verify_code(
    *,
    length: int = settings.email_verification_code_length,
    secret: str = settings.secret.get_secret_value(),
) -> tuple[str, str]:
    """
    Generate a verify code for email verification.

    Returns both the actual value and its HMAC-SHA256 hash.
    Only the latter shall be stored in database.
    """
    code = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )
    return code, get_verify_code_hash(code, secret=secret)
