"""Module for user authentication and management."""

import typing

from fief._exceptions import FiefException
from fief.methods import AuthenticateKwargs, EnrollKwargs, MethodProtocol
from fief.storage import StorageProtocol


class AuthException(FiefException):
    """Base class for all exceptions raised by the auth module."""


class MissingIdentifierFieldsException(AuthException):
    """Exception raised when required identifier fields are missing."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__(f"Missing identifier fields: {fields}")


class UserAlreadyExistsException(AuthException):
    """Exception raised when a user already exists with the given identifier fields."""

    def __init__(self, fields: dict[str, typing.Any]) -> None:
        self.fields = fields
        super().__init__(f"User already exists with identifier fields: {fields}")


class UserProtocol(typing.Protocol):
    id: typing.Any

    @classmethod
    def identifier_fields(cls) -> tuple[str, ...]:  # pragma: no cover
        """
        Return the identifier fields of the user model.

        The values of those fields are used to uniquely identify the user in the system.
        """
        ...


U = typing.TypeVar("U", bound=UserProtocol)
"""Generic type variable for user models."""


class AuthManager(typing.Generic[U]):
    """Class to manage user authentication and methods."""

    def __init__(self, model: type[U], storage: StorageProtocol[U]) -> None:
        self.model = model
        self.storage = storage

    def signup(
        self,
        method: MethodProtocol[EnrollKwargs, AuthenticateKwargs],
        enroll_data: EnrollKwargs,
        **fields: typing.Any,
    ) -> U:
        """
        Sign up a new user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            enroll_data: The data for the method's enroll function.
            **fields: The user fields to create the new user. It must contain
                all the identifier fields.

        Returns:
            The newly created user.

        Raises:
            UserAlreadyExistsException: If a user already exists with the given identifier fields.
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        identifier_fields = self._validate_identifier_fields(fields)

        existing_user = self.storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        if existing_user is not None:
            raise UserAlreadyExistsException(
                {field: fields[field] for field in identifier_fields}
            )

        user = self.storage.create(**fields)
        method.enroll(user.id, enroll_data)

        return user

    def signin(
        self,
        method: MethodProtocol[EnrollKwargs, AuthenticateKwargs],
        auth_data: AuthenticateKwargs,
        **fields: typing.Any,
    ) -> U | None:
        """
        Sign in a user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            auth_data: The data for the method's authenticate function.
            **fields: The fields to identify the user.

        Returns:
            The authenticated user or None if authentication fails.

        Raises:
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        identifier_fields = self._validate_identifier_fields(fields)

        user = self.storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        user_id = user.id if user else None

        if method.authenticate(user_id, auth_data) and user is not None:
            return user

        return None

    def _validate_identifier_fields(
        self, fields: dict[str, typing.Any]
    ) -> tuple[str, ...]:
        identifier_fields = self.model.identifier_fields()
        missing_fields = [field for field in identifier_fields if field not in fields]
        if len(missing_fields) > 0:
            raise MissingIdentifierFieldsException(missing_fields)
        return identifier_fields


__all__ = [
    "U",
    "AuthManager",
    "AuthException",
    "MissingIdentifierFieldsException",
    "UserAlreadyExistsException",
]
