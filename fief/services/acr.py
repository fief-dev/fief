from enum import StrEnum


class ACR(StrEnum):
    """
    List of defined Authentication Context Class Reference.
    """

    LEVEL_ZERO = "0"
    """Level 0. No authentication was performed, a previous session was used."""

    LEVEL_ONE = "1"
    """Level 1. Password authentication was performed."""

    def __lt__(self, other: object) -> bool:
        return self._compare(other, True, True)

    def __le__(self, other: object) -> bool:
        return self._compare(other, False, True)

    def __gt__(self, other: object) -> bool:
        return self._compare(other, True, False)

    def __ge__(self, other: object) -> bool:
        return self._compare(other, False, False)

    def _compare(self, other: object, strict: bool, asc: bool) -> bool:
        if not isinstance(other, ACR):
            return NotImplemented

        if self == other:
            return not strict

        for elem in ACR:
            if self == elem:
                return asc
            elif other == elem:
                return not asc
        raise RuntimeError()
