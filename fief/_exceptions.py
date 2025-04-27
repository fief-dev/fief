class FiefException(Exception):
    """Base class for all exceptions raised by Fief."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


__all__ = [
    "FiefException",
]
