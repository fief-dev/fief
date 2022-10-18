"""We're testing the EmailProvider base class' format_address function, but
we can't instantiate an object of the base type, so we're using Null as
a proxy."""
from fief.services.email.base import format_address


def test_format_address_with_only_email():
    formatted = format_address("test@example.com")
    assert formatted == "test@example.com"


def test_format_address_with_name_and_address():
    formatted = format_address("test@example.com", "Test Person")
    assert formatted == "Test Person <test@example.com>"
