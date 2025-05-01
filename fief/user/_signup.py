import typing

from fief.storage import StorageProtocol

from ._exceptions import UserException
from ._model import U


class SignupException(UserException):
    """Base class for all exceptions raised by the signup module."""


class MissingIdentifierFieldsException(SignupException):
    """Exception raised when identifier fields are missing in the signup process."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__(f"Missing identifier fields: {', '.join(fields)}")


class UserAlreadyExistsException(SignupException):
    """Exception raised when a user already exists with the given identifier fields."""

    def __init__(self, fields: dict[str, typing.Any]) -> None:
        self.fields = fields
        super().__init__(f"User already exists with identifier fields: {fields}")


class Signup(typing.Generic[U]):
    def __init__(self, model: type[U], storage: StorageProtocol[U]) -> None:
        self.model = model
        self.storage = storage

    def signup(self, **kwargs: typing.Any) -> U:
        identifier_fields = self.model.identifier_fields()
        missing_fields = [field for field in identifier_fields if field not in kwargs]
        if len(missing_fields) > 0:
            raise MissingIdentifierFieldsException(missing_fields)

        existing_user = self.storage.get_one(
            **{field: kwargs[field] for field in identifier_fields}
        )
        if existing_user is not None:
            raise UserAlreadyExistsException(
                {field: kwargs[field] for field in identifier_fields}
            )

        return self.storage.create(**kwargs)
