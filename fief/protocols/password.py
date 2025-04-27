import typing

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from fief.storage import StorageProtocol

from ._exceptions import ProtocolException
from ._model import ProtocolModel


class PasswordModelData(typing.TypedDict):
    hashed_password: str


class PasswordModel(ProtocolModel, typing.Protocol):
    type: typing.Literal["password"]
    data: PasswordModelData


PM = typing.TypeVar("PM", bound=PasswordModel)


class PasswordHasherProtocol(typing.Protocol):
    def verify_and_update(
        self, password: str | bytes, hash: str | bytes
    ) -> tuple[bool, str | None]: ...  # pragma: no cover

    def hash(
        self,
        password: str | bytes,
        *,
        salt: bytes | None = None,
    ) -> str: ...  # pragma: no cover


class PasswordException(ProtocolException):
    """Base class for all exceptions raised by the password protocol."""


class AlreadyEnrolledException(PasswordException):
    """Exception raised when a user is already enrolled with a password."""

    def __init__(self, user_id: typing.Any) -> None:
        self.user_id = user_id
        super().__init__(f"User {user_id} already has a password enrolled.")


class Password(typing.Generic[PM]):
    """
    Protocol for password-based authentication.

    Parameters:
        model: The password model class.
        storage: The storage instance to persist password data.
        hasher: The password hasher implementation.
            If None, recommended defaults are used.
    """

    _model: type[PM]
    _storage: StorageProtocol
    _hasher: PasswordHasherProtocol

    def __init__(
        self,
        model: type[PM],
        storage: StorageProtocol,
        hasher: PasswordHasherProtocol | None = None,
    ) -> None:
        self._model = model
        self._storage = storage
        self._hasher = hasher or PasswordHash.recommended()

    def enroll(self, user_id: typing.Any, password: str) -> PM:
        """Enroll a user with a password.

        Args:
            user_id: The user ID.
            password: The password.

        Returns:
            PM: The created password model.

        Raises:
            AlreadyEnrolledException: If the user already has a password enrolled.
        """
        # Check if the user already has a password
        existing_password = self._storage.get_one(
            self._model, user_id=user_id, type="password"
        )
        if existing_password is not None:
            raise AlreadyEnrolledException(user_id)

        # Hash the password
        hashed_password = self._hasher.hash(password)

        return self._storage.create(
            self._model,
            type="password",
            user_id=user_id,
            data={"hashed_password": hashed_password},
        )

    def authenticate(self, user_id: typing.Any | None, password: str) -> bool:
        """Authenticate a user with a password.

        Args:
            user_id: The user ID. It can be None if no user was found by identifier.
            password: The password.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        # Get the password model
        password_model: PM | None = None
        if user_id is not None:
            password_model = self._storage.get_one(
                self._model, user_id=user_id, type="password"
            )

        if user_id is None or password_model is None:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self._hasher.hash(password)
            return False

        # Verify the password
        try:
            is_valid, updated_hash = self._hasher.verify_and_update(
                password, password_model.data["hashed_password"]
            )
        except UnknownHashError:
            return False

        # Update the password hash if needed
        if is_valid and updated_hash is not None:
            self._storage.update(
                self._model,
                password_model.id,
                type="password",
                user_id=user_id,
                data={"hashed_password": updated_hash},
            )

        return is_valid
