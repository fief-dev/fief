from fief._exceptions import FiefException, InvalidRequestException


class MethodException(FiefException):
    """Base class for all exceptions raised by authentication methods."""


class InvalidMethodRequestException(InvalidRequestException):
    """Exception raised when a request to an authentication method is invalid."""
