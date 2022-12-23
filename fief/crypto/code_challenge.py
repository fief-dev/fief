import base64
import hashlib
import secrets


def get_code_verifier_hash(verifier: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(verifier.encode("ascii"))
    digest = hasher.digest()
    b64_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return b64_digest[:-1]  # Remove the padding "=" at the end


def verify_code_verifier(verifier: str, challenge: str, method: str) -> bool:
    if method == "plain":
        return secrets.compare_digest(verifier, challenge)
    elif method == "S256":
        verifier_hash = get_code_verifier_hash(verifier)
        return secrets.compare_digest(verifier_hash, challenge)
    return False  # pragma: no cover
