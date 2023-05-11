from typing import Self

from zxcvbn_rs_py import zxcvbn

from fief.locale import gettext_lazy as _

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_STRENGTH_SCORE = 3


class PasswordValidation:
    def __init__(self, valid: bool, score: int, messages: list[str]) -> None:
        self.valid = valid
        self.score = score
        self.messages = messages or []

    @classmethod
    def validate(cls, password: str) -> Self:
        valid = True
        messages: list[str] = []

        if len(password) < MIN_PASSWORD_LENGTH:
            valid = False
            messages.append(
                _(
                    "Password must be at least %(min)d characters long.",
                    min=MIN_PASSWORD_LENGTH,
                )
            )
        elif len(password) > MAX_PASSWORD_LENGTH:
            valid = False
            messages.append(
                _(
                    "Password must be at most %(max)d characters long.",
                    max=MAX_PASSWORD_LENGTH,
                )
            )

        password_strength = zxcvbn(password[0:MAX_PASSWORD_LENGTH])
        if password_strength.score < MIN_PASSWORD_STRENGTH_SCORE:
            valid = False
            messages.append(_("Password is not strong enough."))

        return cls(valid, password_strength.score, messages)
