from typing import Literal

HYBRID_RESPONSE_TYPES = ["code id_token", "code token", "code id_token token"]
ALLOWED_RESPONSE_TYPES = ["code"] + HYBRID_RESPONSE_TYPES
NONCE_REQUIRED_RESPONSE_TYPES = HYBRID_RESPONSE_TYPES

DEFAULT_RESPONSE_MODE: dict[str, Literal["query", "fragment"]] = {
    "code": "query",
    "code id_token": "fragment",
    "code token": "fragment",
    "code id_token token": "fragment",
}
