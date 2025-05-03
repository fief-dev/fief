import typing

import typing_extensions


class FiefException(Exception):
    """Base class for all exceptions raised by Fief."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ErrorDetails(typing.TypedDict):
    type: str
    """
    The type of error that occurred, this is an identifier designed for
    programmatic use that will change rarely or never.

    `type` is unique for each error message, and can hence be used as an identifier to build custom error messages.
    """
    loc: tuple[int | str, ...]
    """Tuple of strings and ints identifying where in the data the error occurred."""
    msg: str
    """A human readable error message."""
    input: typing.Any
    """The input data at this `loc` that caused the error."""
    ctx: typing_extensions.NotRequired[dict[str, typing.Any]]
    """
    Values which are required to render the error message, and could hence be useful in rendering custom error messages.
    Also useful for passing custom error data forward.
    """


class InvalidRequestException(FiefException):
    """Exception raised when a request is invalid."""

    def __init__(self, errors: list[ErrorDetails]) -> None:
        self.errors = errors
        message = "Invalid request"
        super().__init__(message)


__all__ = [
    "FiefException",
    "ErrorDetails",
    "InvalidRequestException",
]
