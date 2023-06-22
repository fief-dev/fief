from enum import StrEnum


class ACR(StrEnum):
    """
    List of defined Authentication Context Class Reference.
    """

    LEVEL_ZERO = "0"
    """Level 0. No authentication was performed, a previous session was used."""

    LEVEL_ONE = "1"
    """Level 1. Password authentication was performed."""
