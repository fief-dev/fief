import secrets
from typing import Literal

from jwcrypto import jwk


class AuthException(Exception):
    pass


class InvalidAccessToken(AuthException):
    pass


def generate_jwk(kid: str, use: Literal["sig", "enc"]) -> jwk.JWK:
    return jwk.JWK.generate(kty="RSA", size=2048, use=use, kid=kid)


def load_jwk(json: str) -> jwk.JWK:
    return jwk.JWK.from_json(json)


def generate_signature_jwk_string() -> str:
    key = generate_jwk(secrets.token_urlsafe(), "sig")
    return key.export()
