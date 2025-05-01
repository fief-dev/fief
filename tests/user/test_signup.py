import pytest

from fief.user import MissingIdentifierFieldsException, Signup
from fief.user._signup import UserAlreadyExistsException
from tests.fixtures import MockStorage, User


@pytest.fixture
def storage() -> MockStorage[User]:
    return MockStorage(User)


@pytest.fixture
def signup(storage: MockStorage[User]) -> Signup[User]:
    return Signup(User, storage)


class TestSignup:
    def test_missing_identifier_fields(self, signup: Signup[User]) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            signup.signup(name="Aliénor")

    def test_user_already_exists(
        self, signup: Signup[User], storage: MockStorage[User]
    ) -> None:
        storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            signup.signup(email="alienor@aquitaine.duchy")

    def test_valid(self, signup: Signup[User]) -> None:
        user = signup.signup(email="alienor@aquitaine.duchy")
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"
